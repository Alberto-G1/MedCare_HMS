from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def notification_list_view(request):
    notifications = Notification.objects.filter(recipient=request.user)
    # Mark all as read when the user visits this page
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return render(request, 'notifications/notification_list.html', {'notifications': notifications})