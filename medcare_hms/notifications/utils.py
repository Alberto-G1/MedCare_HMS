from .models import Notification

def create_notification(recipient, message, link=None):
    """
    Helper function to create a new notification.
    """
    Notification.objects.create(
        recipient=recipient,
        message=message,
        link=link
    )