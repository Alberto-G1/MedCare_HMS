from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Notification

@login_required
def notification_list_view(request):
    notifications = Notification.objects.filter(recipient=request.user)
    # Mark all as read when the user visits this page
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return render(request, 'notifications/notification_list.html', {'notifications': notifications})


@login_required
def notification_dropdown_data(request):
    unread_qs = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-timestamp')[:10]
    recent_read_qs = Notification.objects.filter(recipient=request.user, is_read=True).order_by('-timestamp')[:5]
    def serialize(qs):
        return [
            {
                'id': n.id,
                'message': n.message,
                'timestamp': n.timestamp.strftime('%Y-%m-%d %H:%M'),
                'link': n.link or '',
                'is_read': n.is_read,
            } for n in qs
        ]
    return JsonResponse({
        'unread': serialize(unread_qs),
        'recent_read': serialize(recent_read_qs),
        'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count()
    })


@login_required
@require_POST
def mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    if not notif.is_read:
        notif.is_read = True
        notif.save(update_fields=['is_read'])
    return JsonResponse({'status': 'ok', 'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count()})


@login_required
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok', 'unread_count': 0})