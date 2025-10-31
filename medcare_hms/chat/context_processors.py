from .models import Thread

def unread_chat_messages(request):
    if request.user.is_authenticated:
        # Get all threads the user participates in
        threads = request.user.chat_threads.all()
        # Count total unread messages across all threads
        total_unread = 0
        for thread in threads:
            total_unread += thread.get_unread_count_for_user(request.user)
        return {'unread_chat_messages_count': total_unread}
    return {'unread_chat_messages_count': 0}