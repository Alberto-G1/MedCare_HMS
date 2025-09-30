# reports/migrations/0002_populate_sample_data.py

from django.db import migrations
from datetime import date, time, timedelta
import random

def create_sample_data(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('accounts', 'UserProfile')
    PatientProfile = apps.get_model('patients', 'PatientProfile')
    DoctorProfile = apps.get_model('doctors', 'DoctorProfile')
    Appointment = apps.get_model('patients', 'Appointment')
    Bill = apps.get_model('billing', 'Bill')
    BillItem = apps.get_model('billing', 'BillItem')

    # --- Create a sample doctor if one doesn't exist ---
    doctor_user, created = User.objects.get_or_create(
        username='sample_doctor', 
        defaults={'first_name': 'Alex', 'last_name': 'Smith'}
    )
    if created:
        UserProfile.objects.create(user=doctor_user, role='DOCTOR')
    doctor_profile, _ = DoctorProfile.objects.get_or_create(user=doctor_user, defaults={'specialization': 'General Practice'})

    # --- Create sample patients ---
    for i in range(10):
        patient_user, created = User.objects.get_or_create(
            username=f'patient_{i}',
            defaults={'first_name': f'Patient', 'last_name': f'{i+1}'}
        )
        if created:
            UserProfile.objects.create(user=patient_user, role='PATIENT')
        PatientProfile.objects.get_or_create(user=patient_user)
    
    patients = PatientProfile.objects.all()

    # --- Create sample appointments and paid bills over the last 3 months ---
    today = date.today()
    for i in range(50): # Create 50 sample appointments
        # Distribute appointments over the last 90 days
        appt_date = today - timedelta(days=random.randint(0, 90))
        appt_time = time(hour=random.randint(9, 16), minute=random.choice([0, 30]))
        patient = random.choice(patients)

        appointment, created = Appointment.objects.get_or_create(
            patient=patient,
            doctor=doctor_profile,
            appointment_date=appt_date,
            appointment_time=appt_time,
            defaults={
                'reason': 'Sample checkup',
                'status': 'Completed'
            }
        )
        
        # Create a paid bill for about 70% of completed appointments
        if not Bill.objects.filter(appointment=appointment).exists() and random.random() < 0.7:
            total_amount = random.randint(50000, 250000)
            bill = Bill.objects.create(
                patient=patient,
                appointment=appointment,
                total_amount=total_amount,
                amount_paid=total_amount,
                status='Paid',
                bill_date=appt_date + timedelta(days=1)
            )
            # Historical model in migrations won't have the BillItem.save override, so
            # we must explicitly set the computed "amount" to avoid NOT NULL errors.
            BillItem.objects.create(
                bill=bill,
                description='Consultation Fee',
                quantity=1,
                unit_price=total_amount,
                amount=total_amount  # quantity * unit_price
            )

class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'), # Make sure this points to your first migration file
        ('accounts', '0001_initial'), # Add dependencies to all relevant apps
        ('patients', '0001_initial'),
        ('doctors', '0001_initial'),
        ('billing', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_sample_data),
    ]