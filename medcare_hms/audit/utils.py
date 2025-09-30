from .models import SystemLog
from django.utils import timezone

SAFE_DETAIL_KEYS = {'before','after','fields','extra'}

def audit_log(actor=None, action='OTHER', target=None, summary='', details=None, request=None, correlation_id=None):
    """Create a system audit log entry.

    Parameters:
        actor (User|None): The user performing the action.
        action (str): One of SystemLog.ACTION_CHOICES.
        target (Model|None): The target model instance (optional).
        summary (str): Short human readable description.
        details (dict|None): Additional structured context.
        request (HttpRequest|None): If provided, capture IP + user agent.
    """
    target_model = None
    target_id = None
    if target is not None:
        target_model = target.__class__.__name__
        target_id = getattr(target, 'pk', None)
    # Sanitize details keys to avoid accidental large dumps
    sanitized = None
    if isinstance(details, dict):
        sanitized = {k: v for k, v in details.items() if k in SAFE_DETAIL_KEYS}
    ip = None
    ua = None
    if request is not None:
        ip = request.META.get('REMOTE_ADDR')
        ua = request.META.get('HTTP_USER_AGENT','')[:255]
        if correlation_id is None:
            correlation_id = getattr(request, 'correlation_id', None)
    SystemLog.objects.create(
        actor=actor,
        action=action,
        target_model=target_model or 'N/A',
        target_id=str(target_id) if target_id is not None else None,
        summary=summary[:255],
        details=sanitized,
        ip_address=ip,
        user_agent=ua,
        created_at=timezone.now(),
        correlation_id=correlation_id
    )
