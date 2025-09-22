from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import UserProfile
from .forms import RegistrationForm 


# A helper function to create users of different roles for our tests
def create_user_with_role(username, password, role, is_active=True):
    """
    Helper function to quickly create a user with an associated UserProfile.
    """
    user = User.objects.create_user(username=username, password=password)
    user.is_active = is_active
    user.save()
    UserProfile.objects.create(user=user, role=role)
    return user

class AuthenticationTests(TestCase):
    """
    Tests for user registration, login, and the approval workflow.
    """

    def test_patient_registration_is_auto_approved(self):
        """
        Ensure that a new user registering with the 'PATIENT' role is automatically active.
        """
        # The client is a dummy web browser
        response = self.client.post(reverse('register'), {
            'username': 'testpatient',
            'email': 'patient@test.com',
            'contact': '1234567890',
            'password': 'testpassword123',
            'confirm_password': 'testpassword123',
            'role': 'PATIENT'
        })
        
        # After registration, the user should be redirected
        self.assertEqual(response.status_code, 302, "Registration should redirect.")
        
        # Check that the user was created and is active
        new_user = User.objects.get(username='testpatient')
        self.assertTrue(new_user.is_active, "Patient should be active immediately after registration.")
        self.assertEqual(new_user.userprofile.role, 'PATIENT')

    def test_doctor_registration_requires_approval(self):
        """
        Ensure that a new user registering with the 'DOCTOR' role is NOT active by default.
        """
        self.client.post(reverse('register'), {
            'username': 'testdoctor',
            'email': 'doctor@test.com',
            'contact': '0987654321',
            'password': 'testpassword123',
            'confirm_password': 'testpassword123',
            'role': 'DOCTOR'
        })
        
        new_user = User.objects.get(username='testdoctor')
        self.assertFalse(new_user.is_active, "Doctor should be inactive and require admin approval.")
        self.assertEqual(new_user.userprofile.role, 'DOCTOR')
    # In accounts/tests.py, inside AuthenticationTests class


    def test_registration_form_password_mismatch(self):
        """
        Test that the RegistrationForm raises a validation error if passwords do not match.
        """
        form_data = {
            'username': 'testuser',
            'email': 'test@email.com',
            'contact': '12345',
            'password': 'password123',
            'confirm_password': 'password456', # Mismatched password
            'role': 'PATIENT'
        }
        form = RegistrationForm(data=form_data)
        
        # Assert that the form is NOT valid
        self.assertFalse(form.is_valid())
        
        # Assert that the correct error message is present for the 'confirm_password' field
        self.assertIn('confirm_password', form.errors)
        self.assertEqual(form.errors['confirm_password'][0], "Passwords do not match.")

class DashboardAccessTests(TestCase):
    """
    Tests for role-based access control to ensure users can only access their own dashboards.
    """
    
    def setUp(self):
        """
        The setUp method runs before every single test in this class.
        It's perfect for creating objects that will be used in multiple tests.
        """
        self.patient_user = create_user_with_role('patientuser', 'password', 'PATIENT')
        self.doctor_user = create_user_with_role('doctoruser', 'password', 'DOCTOR')
        self.admin_user = create_user_with_role('adminuser', 'password', 'ADMIN')

    def test_patient_can_access_patient_dashboard(self):
        """A logged-in patient should be able to access their own dashboard."""
        self.client.login(username='patientuser', password='password')
        response = self.client.get(reverse('patient_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_patient_cannot_access_doctor_dashboard(self):
        """A patient should be redirected if they try to access the doctor dashboard."""
        self.client.login(username='patientuser', password='password')
        response = self.client.get(reverse('doctor_dashboard'))
        # 302 means a redirect. The user is redirected because the @doctor_required decorator failed.
        self.assertEqual(response.status_code, 302, "Patient should be redirected from doctor dashboard.")

    def test_patient_cannot_access_admin_dashboard(self):
        """A patient should be redirected from the admin dashboard."""
        self.client.login(username='patientuser', password='password')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_doctor_can_access_doctor_dashboard(self):
        """A logged-in doctor should be able to access their own dashboard."""
        self.client.login(username='doctoruser', password='password')
        response = self.client.get(reverse('doctor_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_is_redirected_from_dashboards(self):
        """A user who is not logged in should be redirected to the login page from any dashboard."""
        response = self.client.get(reverse('patient_dashboard'))
        # The redirect URL should contain the login page URL
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('patient_dashboard')}")
        
        response = self.client.get(reverse('doctor_dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('doctor_dashboard')}")
        
        response = self.client.get(reverse('admin_dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('admin_dashboard')}")