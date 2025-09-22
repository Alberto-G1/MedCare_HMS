from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Thread, ChatMessage
from accounts.tests import create_user_with_role

class ChatModelTest(TestCase):
    
    def test_thread_creation(self):
        """Test creating a thread and adding participants."""
        user1 = User.objects.create_user(username='user1', password='pw')
        user2 = User.objects.create_user(username='user2', password='pw')
        thread = Thread.objects.create()
        thread.participants.add(user1, user2)
        
        self.assertEqual(Thread.objects.count(), 1)
        self.assertEqual(thread.participants.count(), 2)
        self.assertIn(user1, thread.participants.all())

class ChatViewsTest(TestCase):
    
    def setUp(self):
        self.user_a = create_user_with_role('userA', 'password', 'PATIENT')
        self.user_b = create_user_with_role('userB', 'password', 'DOCTOR')
        self.user_c = create_user_with_role('userC', 'password', 'PATIENT')
        
        # Create a thread between user A and user B
        self.thread = Thread.objects.create()
        self.thread.participants.add(self.user_a, self.user_b)
    
    def test_start_chat_view_creates_new_thread(self):
        """Test that visiting the start_chat URL creates a new thread if one doesn't exist."""
        self.client.login(username='userA', password='password')
        
        # There's no thread between A and C yet
        self.assertEqual(Thread.objects.filter(participants=self.user_a).filter(participants=self.user_c).count(), 0)
        
        # User A starts a chat with User C
        response = self.client.get(reverse('chat:start_chat', kwargs={'user_id': self.user_c.id}))
        
        # Check that a new thread was created
        self.assertEqual(Thread.objects.filter(participants=self.user_a).filter(participants=self.user_c).count(), 1)
        new_thread = Thread.objects.get(participants=self.user_a, participants=self.user_c)
        self.assertRedirects(response, reverse('chat:thread_detail', kwargs={'thread_id': new_thread.id}))

    def test_start_chat_view_finds_existing_thread(self):
        """Test that the start_chat URL redirects to an existing thread."""
        self.client.login(username='userA', password='password')
        
        # A thread already exists between A and B
        response = self.client.get(reverse('chat:start_chat', kwargs={'user_id': self.user_b.id}))
        
        # It should not create a new thread, but redirect to the existing one
        self.assertEqual(Thread.objects.count(), 1) # Still only 1 thread in the DB
        self.assertRedirects(response, reverse('chat:thread_detail', kwargs={'thread_id': self.thread.id}))

    def test_user_cannot_access_unrelated_thread(self):
        """A user should be redirected if they try to view a chat they are not part of."""
        self.client.login(username='userC', password='password')
        
        # User C tries to access the thread between A and B
        response = self.client.get(reverse('chat:thread_detail', kwargs={'thread_id': self.thread.id}))
        
        self.assertRedirects(response, reverse('chat:thread_list'), 
            msg_prefix="User C should be redirected from a thread they don't belong to.")

    def test_thread_list_shows_correct_threads(self):
        """The thread list should only show threads the logged-in user is a participant of."""
        self.client.login(username='userA', password='password')
        response = self.client.get(reverse('chat:thread_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/thread_list.html')
        # The context should contain the thread between A and B
        self.assertIn(self.thread, response.context['threads'])