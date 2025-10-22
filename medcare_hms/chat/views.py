from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Thread, UserPresence, CannedResponse, ChatMessage
from django.db.models import Max, Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import os

@login_required
def thread_list_view(request, thread_id=None):
    # Get all threads the user is a part of
    user_threads = Thread.objects.filter(participants=request.user).order_by('-updated')
    
    # --- NEW LOGIC: Prepare the data for the template ---
    threads_with_other_user = []
    total_unread = 0
    
    for thread in user_threads:
        # For each thread, find the participant who is not the current user
        other_participant = thread.participants.exclude(id=request.user.id).first()
        
        # We also want the last message to display
        last_message = thread.messages.order_by('-timestamp').first()
        
        # Get unread count for this thread
        unread_count = thread.get_unread_count_for_user(request.user)
        total_unread += unread_count
        
        # Check if other user is online
        is_online = False
        if other_participant:
            try:
                is_online = other_participant.presence.is_online
            except UserPresence.DoesNotExist:
                is_online = False

        threads_with_other_user.append({
            'thread_object': thread,
            'other_user': other_participant,
            'last_message': last_message,
            'unread_count': unread_count,
            'is_online': is_online
        })

    # If thread_id is provided, load that thread's details
    active_thread = None
    messages = []
    other_user = None
    patient_context = None
    is_online = False
    last_seen = None
    canned_responses = []
    
    if thread_id:
        try:
            active_thread = Thread.objects.get(pk=thread_id, participants=request.user)
            other_user = active_thread.participants.exclude(id=request.user.id).first()
            
            # Get patient context if applicable
            if other_user:
                try:
                    if hasattr(other_user, 'patientprofile'):
                        patient_profile = other_user.patientprofile
                        patient_context = {
                            'name': other_user.get_full_name(),
                            'age': patient_profile.age if hasattr(patient_profile, 'age') else 'N/A',
                            'gender': patient_profile.gender if hasattr(patient_profile, 'gender') else 'N/A',
                            'blood_group': patient_profile.blood_group if hasattr(patient_profile, 'blood_group') else 'N/A',
                            'contact': other_user.userprofile.contact if hasattr(other_user, 'userprofile') else 'N/A'
                        }
                except Exception:
                    pass
                
                # Check online status
                try:
                    presence = other_user.presence
                    is_online = presence.is_online
                    last_seen = presence.last_seen
                except UserPresence.DoesNotExist:
                    pass
            
            # Get messages
            messages = active_thread.messages.order_by('timestamp').select_related(
                'sender__doctorprofile', 
                'sender__patientprofile',
                'sender__receptionistprofile'
            )
            
            # Get canned responses
            if request.user.groups.filter(name__in=['Doctors', 'Receptionists', 'Admins']).exists():
                canned_responses = CannedResponse.objects.filter(
                    Q(created_by=request.user) | Q(created_by__is_staff=True),
                    is_active=True
                )
        except Thread.DoesNotExist:
            pass

    context = {
        'threads': threads_with_other_user,
        'total_unread': total_unread,
        'active_thread': active_thread,
        'messages': messages,
        'other_user': other_user,
        'patient_context': patient_context,
        'is_online': is_online,
        'last_seen': last_seen,
        'canned_responses': canned_responses
    }
    return render(request, 'chat/combined_chat.html', context)

@login_required
def thread_detail_view(request, thread_id):
    thread = get_object_or_404(Thread, pk=thread_id)
    if request.user not in thread.participants.all():
        return redirect('chat:thread_list')
    
    # Get the other user in the thread
    other_user = thread.participants.exclude(id=request.user.id).first()
    
    # Get patient context if applicable
    patient_context = None
    if other_user:
        try:
            # If the other user is a patient, get their profile
            if hasattr(other_user, 'patientprofile'):
                patient_profile = other_user.patientprofile
                patient_context = {
                    'name': other_user.get_full_name(),
                    'age': patient_profile.age if hasattr(patient_profile, 'age') else 'N/A',
                    'gender': patient_profile.gender if hasattr(patient_profile, 'gender') else 'N/A',
                    'blood_group': patient_profile.blood_group if hasattr(patient_profile, 'blood_group') else 'N/A',
                    'contact': other_user.userprofile.contact if hasattr(other_user, 'userprofile') else 'N/A'
                }
        except Exception as e:
            pass
    
    # Check if other user is online
    is_online = False
    last_seen = None
    if other_user:
        try:
            presence = other_user.presence
            is_online = presence.is_online
            last_seen = presence.last_seen
        except UserPresence.DoesNotExist:
            pass
    
    # Get all messages and optimize by prefetching related user profiles
    messages = thread.messages.order_by('timestamp').select_related(
        'sender__doctorprofile', 
        'sender__patientprofile',
        'sender__receptionistprofile'
    )
    
    # Get canned responses for staff members (doctors, receptionists)
    canned_responses = []
    if request.user.groups.filter(name__in=['Doctors', 'Receptionists', 'Admins']).exists():
        canned_responses = CannedResponse.objects.filter(
            Q(created_by=request.user) | Q(created_by__is_staff=True),
            is_active=True
        )

    context = {
        'thread': thread,
        'messages': messages,
        'other_user': other_user,  # Pass the other user object
        'patient_context': patient_context,  # Pass patient context
        'is_online': is_online,  # Pass online status
        'last_seen': last_seen,  # Pass last seen timestamp
        'canned_responses': canned_responses  # Pass canned responses
    }
    return render(request, 'chat/thread_detail.html', context)

@login_required
def start_chat_view(request, user_id):
    receiver = get_object_or_404(User, pk=user_id)
    # Find existing thread or create a new one
    thread = Thread.objects.filter(participants=request.user).filter(participants=receiver).first()
    if not thread:
        thread = Thread.objects.create()
        thread.participants.add(request.user, receiver)
    return redirect('chat:thread_detail', thread_id=thread.id)

@login_required
@require_POST
def upload_file_view(request):
    """Handle file uploads for chat messages"""
    try:
        thread_id = request.POST.get('thread_id')
        message_text = request.POST.get('message', '')
        attachment = request.FILES.get('attachment')
        
        if not thread_id or not attachment:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Get the thread and verify user is a participant
        thread = get_object_or_404(Thread, pk=thread_id)
        if request.user not in thread.participants.all():
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Determine attachment type
        file_ext = os.path.splitext(attachment.name)[1].lower()
        attachment_type = 'file'
        if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            attachment_type = 'image'
        elif file_ext == '.pdf':
            attachment_type = 'pdf'
        elif file_ext in ['.doc', '.docx', '.txt']:
            attachment_type = 'document'
        elif file_ext in ['.mp4', '.avi', '.mov', '.webm']:
            attachment_type = 'video'
        
        # Create the message with attachment
        chat_message = ChatMessage.objects.create(
            thread=thread,
            sender=request.user,
            message=message_text,
            attachment=attachment,
            attachment_type=attachment_type
        )
        
        # Get sender's avatar
        sender_avatar = '/media/profile_pictures/default.jpeg'
        try:
            if hasattr(request.user, 'doctorprofile') and request.user.doctorprofile.profile_picture:
                sender_avatar = request.user.doctorprofile.profile_picture.url
            elif hasattr(request.user, 'patientprofile') and request.user.patientprofile.profile_picture:
                sender_avatar = request.user.patientprofile.profile_picture.url
            elif hasattr(request.user, 'receptionistprofile') and request.user.receptionistprofile.profile_picture:
                sender_avatar = request.user.receptionistprofile.profile_picture.url
        except:
            pass
        
        # Broadcast the message via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{thread_id}',
            {
                'type': 'chat_message',
                'message': message_text,
                'sender': request.user.username,
                'sender_name': request.user.get_full_name() or request.user.username,
                'sender_avatar': sender_avatar,
                'message_id': chat_message.id,
                'timestamp': chat_message.timestamp.isoformat(),
                'attachment_url': chat_message.attachment.url if chat_message.attachment else None,
                'attachment_type': attachment_type,
                'attachment_name': attachment.name,
                'attachment_size': f'{attachment.size / 1024:.1f} KB' if attachment.size < 1024*1024 else f'{attachment.size / (1024*1024):.1f} MB'
            }
        )
        
        return JsonResponse({
            'status': 'success',
            'message_id': chat_message.id,
            'attachment_url': chat_message.attachment.url
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)