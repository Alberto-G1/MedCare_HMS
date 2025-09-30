from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from audit.utils import audit_log

# LOGIN / LOGOUT
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    audit_log(actor=user, action='LOGIN', summary='User login', request=request)

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    audit_log(actor=user, action='LOGOUT', summary='User logout', request=request)

# Generic CRUD logging for selected models
TRACKED_MODELS = [
    'patients.Appointment',
    'billing.Bill',
    'billing.BillItem',
    'prescriptions.Prescription',
]

def _is_tracked(instance):
    label = f"{instance._meta.app_label}.{instance.__class__.__name__}"
    return label in TRACKED_MODELS

@receiver(post_save)
def model_saved(sender, instance, created, **kwargs):
    if not _is_tracked(instance):
        return
    action = 'CREATE' if created else 'UPDATE'
    audit_log(actor=getattr(instance, 'updated_by', None), action=action, target=instance, summary=f'{action} {sender.__name__}')

@receiver(post_delete)
def model_deleted(sender, instance, **kwargs):
    if not _is_tracked(instance):
        return
    audit_log(actor=getattr(instance, 'updated_by', None), action='DELETE', target=instance, summary=f'DELETE {sender.__name__}')
