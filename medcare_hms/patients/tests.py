# patients/tests.py

from django.test import TestCase
from django.urls import reverse
from datetime import date, time, timedelta
from .models import PatientProfile, Appointment
from .forms import AppointmentBookingForm, PatientProfileForm
from doctors.models import DoctorProfile
from accounts.tests import create_user_with_role

class PatientProfileAndAppointmentModelTest(TestCase):

    def setUp(self):
        self.patient_user = create_user_with_role('test_patient', 'password', 'PATIENT')
        self.doctor_user = create_user_with_role('test_doctor', 'password', 'DOCTOR')
        PatientProfile.objects.create(user=self.patient_user)
        DoctorProfile.objects.create(user=self.doctor_user, specialization='Dermatology')
    
    def test_appointment_creation(self):
        """Test creating an appointment instance."""
        patient_profile = PatientProfile.objects.get(user=self.patient_user)
        doctor_profile = DoctorProfile.objects.get(user=self.doctor_user)
        appointment = Appointment.objects.create(
            patient=patient_profile,
            doctor=doctor_profile,
            appointment_date=date.today(),
            appointment_time=time(10, 0),
            reason="Skin check"
        )
        self.assertEqual(Appointment.objects.count(), 1)
        self.assertEqual(appointment.patient, patient_profile)
        self.assertEqual(appointment.status, 'Pending')

class PatientViewsTest(TestCase):

    def setUp(self):
        self.patient_user = create_user_with_role('view_patient', 'password', 'PATIENT')
        self.doctor_user = create_user_with_role('view_doctor', 'password', 'DOCTOR')
        PatientProfile.objects.create(user=self.patient_user)
        DoctorProfile.objects.create(user=self.doctor_user, specialization='Cardiology')
    
    def test_patient_can_book_appointment(self):
        """Test that a patient can successfully book an appointment."""
        self.client.login(username='view_patient', password='password')
        
        appointment_date = date.today() + timedelta(days=5)
        form_data = {
            'doctor': DoctorProfile.objects.first().pk,
            'appointment_date': appointment_date.strftime('%Y-%m-%d'),
            'appointment_time': '14:30',
            'reason': 'Annual checkup'
        }
        
        response = self.client.post(reverse('patients:book_appointment'), data=form_data)
        self.assertRedirects(response, reverse('patients:my_appointments'))
        self.assertEqual(Appointment.objects.count(), 1)
        new_appointment = Appointment.objects.first()
        self.assertEqual(new_appointment.patient.user, self.patient_user)
        self.assertEqual(new_appointment.reason, 'Annual checkup')

    def test_doctor_cannot_book_appointment_via_patient_form(self):
        """A doctor should be redirected from the patient's booking page."""
        self.client.login(username='view_doctor', password='password')
        response = self.client.get(reverse('patients:book_appointment'))
        self.assertEqual(response.status_code, 302, "Doctor should be redirected.")

class PatientFormsTest(TestCase):

    def test_appointment_booking_in_the_past(self):
        """Test that the appointment form rejects dates in the past."""
        past_date = date.today() - timedelta(days=1)
        form_data = {
            'doctor': 1, 'appointment_date': past_date.strftime('%Y-%m-%d'), 
            'appointment_time': '10:00', 'reason': 'test'
        }
        form = AppointmentBookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('appointment_date', form.errors)
        self.assertEqual(form.errors['appointment_date'][0], "Appointment date cannot be in the past.")