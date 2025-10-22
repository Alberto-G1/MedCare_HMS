from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import Notification
from .utils import create_notification
from accounts.tests import create_user_with_role
from datetime import timedelta


class NotificationModelTest(TestCase):
    """Test suite for Notification model"""
    
    def setUp(self):
        """Set up test users"""
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')
    
    def test_notification_creation(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            recipient=self.user1,
            message="This is a test message",
            link="/test/link/"
        )
        
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notification.recipient, self.user1)
        self.assertFalse(notification.is_read)
        self.assertEqual(notification.message, "This is a test message")
    
    def test_notification_string_representation(self):
        """Test notification __str__ method"""
        notification = Notification.objects.create(
            recipient=self.user1,
            message="Test alert"
        )
        
        expected = f"Notification for {self.user1.username}: Test alert"
        self.assertEqual(str(notification), expected)
    
    def test_notification_ordering(self):
        """Test that notifications are ordered by timestamp (newest first)"""
        old_notification = Notification.objects.create(
            recipient=self.user1,
            message="Old message"
        )
        # Make it older
        old_notification.timestamp = timezone.now() - timedelta(hours=2)
        old_notification.save()
        
        new_notification = Notification.objects.create(
            recipient=self.user1,
            message="New message"
        )
        
        notifications = Notification.objects.filter(recipient=self.user1)
        self.assertEqual(notifications.first(), new_notification)
        self.assertEqual(notifications.last(), old_notification)
    
    def test_notification_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            recipient=self.user1,
            message="Test message"
        )
        
        self.assertFalse(notification.is_read)
        
        notification.is_read = True
        notification.save()
        
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
    
    def test_notification_with_url(self):
        """Test notification with action URL"""
        notification = Notification.objects.create(
            recipient=self.user1,
            message="You have an appointment tomorrow",
            link="/appointments/123/"
        )
        
        self.assertEqual(notification.link, "/appointments/123/")
    
    def test_notification_types(self):
        """Test different notification messages"""
        messages = ['Info message', 'Warning message', 'Success message', 'Error message']
        
        for msg in messages:
            Notification.objects.create(
                recipient=self.user1,
                message=msg
            )
        
        self.assertEqual(Notification.objects.count(), 4)


class NotificationUtilsTest(TestCase):
    """Test suite for notification utility functions"""
    
    def setUp(self):
        """Set up test users"""
        self.user = User.objects.create_user(username='testuser', password='password')
    
    def test_create_notification_utility(self):
        """Test the create_notification utility function"""
        create_notification(
            recipient=self.user,
            message="Testing notification creation utility",
            link="/test/"
        )
        
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.first()
        self.assertEqual(notification.message, "Testing notification creation utility")
        self.assertEqual(notification.recipient, self.user)
    
    def test_create_notification_with_url(self):
        """Test creating notification with action URL"""
        create_notification(
            recipient=self.user,
            message="You have a new action",
            link="/actions/1/"
        )
        
        notification = Notification.objects.first()
        self.assertEqual(notification.link, "/actions/1/")


class NotificationViewsTest(TestCase):
    """Test suite for notification views"""
    
    def setUp(self):
        """Set up test user and notifications"""
        self.user = create_user_with_role('testuser', 'password', 'PATIENT')
        
        # Create some notifications
        for i in range(5):
            Notification.objects.create(
                recipient=self.user,
                message=f"Test message {i}"
            )
    
    def test_notification_list_view(self):
        """Test notification list view"""
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('notifications:notification_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notifications/notification_list.html')
        self.assertIn('notifications', response.context)
        self.assertEqual(len(response.context['notifications']), 5)
    
    def test_notification_list_requires_login(self):
        """Test that notification list requires authentication"""
        response = self.client.get(reverse('notifications:notification_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_notification_list_shows_only_user_notifications(self):
        """Test that users only see their own notifications"""
        other_user = create_user_with_role('otheruser', 'password', 'DOCTOR')
        
        # Create notification for other user
        Notification.objects.create(
            recipient=other_user,
            message="Should not be visible"
        )
        
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('notifications:notification_list'))
        
        # Should still only see 5 notifications (not 6)
        self.assertEqual(len(response.context['notifications']), 5)
    
    def test_notification_marks_as_read_on_view(self):
        """Test that viewing notifications marks them as read"""
        self.client.login(username='testuser', password='password')
        
        # All notifications should be unread initially
        unread_count = Notification.objects.filter(
            recipient=self.user, 
            is_read=False
        ).count()
        self.assertEqual(unread_count, 5)
        
        # View the notification list
        response = self.client.get(reverse('notifications:notification_list'))
        
        # All notifications should now be marked as read
        unread_count = Notification.objects.filter(
            recipient=self.user, 
            is_read=False
        ).count()
        self.assertEqual(unread_count, 0)
    
    def test_notification_list_shows_unread_count(self):
        """Test that notification list shows unread count in context"""
        self.client.login(username='testuser', password='password')
        
        # Verify there are 5 unread notifications before the request
        unread_before = Notification.objects.filter(recipient=self.user, is_read=False).count()
        self.assertEqual(unread_before, 5)
        
        # Access the notification list
        response = self.client.get(reverse('notifications:notification_list'))
        
        # The view marks all notifications as read when visited, so unread_notifications_count will be 0
        self.assertIn('unread_notifications_count', response.context)
        self.assertEqual(response.context['unread_notifications_count'], 0)
        
        # Verify all notifications are now marked as read
        unread_after = Notification.objects.filter(recipient=self.user, is_read=False).count()
        self.assertEqual(unread_after, 0)
    
    def test_notification_ordering_newest_first(self):
        """Test that notifications are displayed newest first"""
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('notifications:notification_list'))
        
        notifications = response.context['notifications']
        # Notifications should be ordered by timestamp descending
        for i in range(len(notifications) - 1):
            self.assertGreaterEqual(
                notifications[i].timestamp,
                notifications[i + 1].timestamp
            )


class NotificationIntegrationTest(TestCase):
    """Integration tests for notification system"""
    
    def setUp(self):
        """Set up test users"""
        self.patient = create_user_with_role('patient1', 'password', 'PATIENT')
        self.doctor = create_user_with_role('doctor1', 'password', 'DOCTOR')
    
    def test_notification_created_for_new_message(self):
        """Test that notification is created when user receives a new message"""
        # This would be called from chat consumer
        create_notification(
            recipient=self.patient,
            message=f"You have a new message from Dr. {self.doctor.get_full_name()}",
            link=f"/chat/thread/1/"
        )
        
        notifications = Notification.objects.filter(recipient=self.patient)
        self.assertEqual(notifications.count(), 1)
        self.assertIn("new message", notifications.first().message)
    
    def test_notification_created_for_appointment(self):
        """Test notification for appointment-related events"""
        create_notification(
            recipient=self.patient,
            message="Your appointment has been confirmed for tomorrow at 10:00 AM",
            link="/appointments/"
        )
        
        notification = Notification.objects.first()
        self.assertEqual(notification.recipient, self.patient)
    
    def test_multiple_notifications_for_user(self):
        """Test handling multiple notifications for same user"""
        notification_data = [
            ("Appointment Reminder: Tomorrow at 10 AM", "/appointments/"),
            ("Lab Results Ready: Your results are ready", "/results/"),
            ("Payment Due: Your payment is due", "/billing/"),
        ]
        
        for message, link in notification_data:
            create_notification(
                recipient=self.patient,
                message=message,
                link=link
            )
        
        self.assertEqual(
            Notification.objects.filter(recipient=self.patient).count(),
            3
        )

