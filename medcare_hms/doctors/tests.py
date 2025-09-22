# doctors/tests.py

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import DoctorProfile
from .forms import DoctorProfileForm
from accounts.tests import create_user_with_role # Import the helper function

class DoctorProfileModelTest(TestCase):
    
    def test_doctor_profile_creation(self):
        """Test that a DoctorProfile is created and linked correctly to a User."""
        user = User.objects.create_user(username='testdoc', password='password')
        profile = DoctorProfile.objects.create(
            user=user,
            specialization='Cardiology',
            years_of_experience=10
        )
        self.assertEqual(profile.user.username, 'testdoc')
        self.assertEqual(str(profile), f"Dr. {user.first_name} {user.last_name}")
        self.assertEqual(DoctorProfile.objects.count(), 1)
        self.assertEqual(user.doctorprofile, profile)

class DoctorViewsTest(TestCase):
    
    def setUp(self):
        """Set up users with different roles for access control tests."""
        self.doctor_user = create_user_with_role('doc_user', 'password', 'DOCTOR')
        self.patient_user = create_user_with_role('pat_user', 'password', 'PATIENT')
        DoctorProfile.objects.create(user=self.doctor_user, specialization='Pediatrics')

    def test_doctor_can_access_own_profile(self):
        """Test that a logged-in doctor can view their own profile page."""
        self.client.login(username='doc_user', password='password')
        response = self.client.get(reverse('doctors:doctor_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'doctors/doctor_profile.html')
        self.assertContains(response, "My Profile")
        self.assertContains(response, "Pediatrics")

    def test_patient_cannot_access_doctor_profile_pages(self):
        """Test that a patient is redirected from doctor-specific pages."""
        self.client.login(username='pat_user', password='password')
        
        # Test doctor profile view
        response = self.client.get(reverse('doctors:doctor_profile'))
        self.assertEqual(response.status_code, 302, "Patient should be redirected from doctor profile.")
        
        # Test doctor appointments view
        response = self.client.get(reverse('doctors:doctor_appointments'))
        self.assertEqual(response.status_code, 302, "Patient should be redirected from doctor appointments.")

    def test_doctor_can_update_profile(self):
        """Test that a doctor can successfully POST data to update their profile."""
        self.client.login(username='doc_user', password='password')
        profile = DoctorProfile.objects.get(user=self.doctor_user)
        
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'specialization': 'Oncology',
            'license_number': 'LIC12345',
            'years_of_experience': 15,
            'availability': 'Mon-Wed, 9am-3pm'
        }
        
        response = self.client.post(reverse('doctors:edit_doctor_profile'), data=form_data)
        self.assertRedirects(response, reverse('doctors:doctor_profile'))
        
        # Refresh the profile from the database and check if the data was updated
        profile.refresh_from_db()
        self.doctor_user.refresh_from_db()
        
        self.assertEqual(self.doctor_user.first_name, 'John')
        self.assertEqual(profile.specialization, 'Oncology')
        self.assertEqual(profile.years_of_experience, 15)

class DoctorFormsTest(TestCase):

    def test_doctor_profile_form_valid(self):
        """Test that the DoctorProfileForm is valid with correct data."""
        user = create_user_with_role('form_doc', 'password', 'DOCTOR')
        form_data = {
            'first_name': 'Jane', 'last_name': 'Smith', 'specialization': 'Neurology',
            'license_number': 'LIC54321', 'years_of_experience': 5, 'availability': 'Weekends'
        }
        form = DoctorProfileForm(data=form_data, instance=user.doctorprofile)
        self.assertTrue(form.is_valid())

    def test_doctor_profile_form_invalid_data(self):
        """Test that the form is invalid if required fields are missing."""
        user = create_user_with_role('form_doc2', 'password', 'DOCTOR')
        form_data = {'first_name': 'Jane'} # Missing last name and specialization
        form = DoctorProfileForm(data=form_data, instance=user.doctorprofile)
        self.assertFalse(form.is_valid())
        self.assertIn('last_name', form.errors)
        self.assertIn('specialization', form.errors)