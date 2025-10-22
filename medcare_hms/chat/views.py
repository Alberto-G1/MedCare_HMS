from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Thread, UserPresence, CannedResponse
from django.db.models import Max, Q

@login_required
def thread_list_view(request):
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

    context = {
        # Pass this new, prepared list to the template
        'threads': threads_with_other_user,
        'total_unread': total_unread
    }
    return render(request, 'chat/thread_list.html', context)

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