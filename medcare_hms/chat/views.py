from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Thread
from django.db.models import Max

@login_required
def thread_list_view(request):
    # Get all threads the user is a part of
    user_threads = Thread.objects.filter(participants=request.user).order_by('-updated')
    
    # --- NEW LOGIC: Prepare the data for the template ---
    threads_with_other_user = []
    for thread in user_threads:
        # For each thread, find the participant who is not the current user
        other_participant = thread.participants.exclude(id=request.user.id).first()
        
        # We also want the last message to display
        last_message = thread.messages.order_by('-timestamp').first()

        threads_with_other_user.append({
            'thread_object': thread,
            'other_user': other_participant,
            'last_message': last_message
        })

    context = {
        # Pass this new, prepared list to the template
        'threads': threads_with_other_user 
    }
    return render(request, 'chat/thread_list.html', context)

@login_required
def thread_detail_view(request, thread_id):
    thread = get_object_or_404(Thread, pk=thread_id)
    if request.user not in thread.participants.all():
        return redirect('chat:thread_list')
    
    # Get the other user in the thread
    other_user = thread.participants.exclude(id=request.user.id).first()
    
    # Get all messages and optimize by prefetching related user profiles
    messages = thread.messages.order_by('timestamp').select_related(
        'sender__doctorprofile', 
        'sender__patientprofile',
        'sender__receptionistprofile'
    )

    context = {
        'thread': thread,
        'messages': messages,
        'other_user': other_user, # Pass the other user object
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