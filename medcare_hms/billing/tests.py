from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from .models import Bill, BillItem
from patients.models import PatientProfile, Appointment
from doctors.models import DoctorProfile
from accounts.tests import create_user_with_role


class BillModelTest(TestCase):
    """Test suite for Bill model"""
    
    def setUp(self):
        """Set up test data"""
        # Clear any existing data
        Bill.objects.all().delete()
        BillItem.objects.all().delete()
        
        self.patient_user = create_user_with_role('patient1', 'password', 'PATIENT')
        self.doctor_user = create_user_with_role('doctor1', 'password', 'DOCTOR')
        
        self.patient = PatientProfile.objects.create(user=self.patient_user)
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            specialization='General Medicine'
        )
    
    def test_bill_creation(self):
        """Test creating a bill"""
        bill = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal('100.00'),
            amount_paid=Decimal('0.00'),
            status='Unpaid'
        )
        
        self.assertEqual(Bill.objects.count(), 1)
        self.assertEqual(bill.patient, self.patient)
        self.assertEqual(bill.status, 'Unpaid')
        self.assertEqual(bill.total_amount, Decimal('100.00'))
    
    def test_bill_string_representation(self):
        """Test bill __str__ method"""
        bill = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal('100.00')
        )
        
        expected = f"Bill #{bill.pk} for {self.patient.user.username}"
        self.assertEqual(str(bill), expected)
    
    def test_bill_amount_due_property(self):
        """Test amount_due calculated property"""
        bill = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal('100.00'),
            amount_paid=Decimal('30.00')
        )
        
        self.assertEqual(bill.amount_due, Decimal('70.00'))
    
    def test_bill_amount_due_fully_paid(self):
        """Test amount_due when bill is fully paid"""
        bill = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal('100.00'),
            amount_paid=Decimal('100.00'),
            status='Paid'
        )
        
        self.assertEqual(bill.amount_due, Decimal('0.00'))
    
    def test_bill_with_appointment(self):
        """Test creating bill linked to appointment"""
        from datetime import time
        
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(10, 0),
            reason="Checkup"
        )
        
        bill = Bill.objects.create(
            patient=self.patient,
            appointment=appointment,
            total_amount=Decimal('150.00')
        )
        
        self.assertEqual(bill.appointment, appointment)
    
    def test_bill_status_choices(self):
        """Test different bill status options"""
        statuses = ['Unpaid', 'Paid', 'Partially Paid']
        
        for status in statuses:
            bill = Bill.objects.create(
                patient=self.patient,
                total_amount=Decimal('100.00'),
                status=status
            )
            self.assertEqual(bill.status, status)
    
    def test_bill_payment_methods(self):
        """Test different payment method options"""
        payment_methods = ['Cash', 'Card', 'MTN Mobile Money', 'Airtel Money', 'Insurance']
        
        for method in payment_methods:
            bill = Bill.objects.create(
                patient=self.patient,
                total_amount=Decimal('100.00'),
                payment_method=method
            )
            self.assertEqual(bill.payment_method, method)
    
    def test_bill_due_date(self):
        """Test bill with due date"""
        due_date = date.today() + timedelta(days=30)
        bill = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal('200.00'),
            due_date=due_date
        )
        
        self.assertEqual(bill.due_date, due_date)
    
    def test_bill_auto_timestamps(self):
        """Test that created_at and updated_at are set automatically"""
        bill = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal('100.00')
        )
        
        self.assertIsNotNone(bill.created_at)
        self.assertIsNotNone(bill.updated_at)
        self.assertIsNotNone(bill.bill_date)


class BillItemModelTest(TestCase):
    """Test suite for BillItem model"""
    
    def setUp(self):
        """Set up test data"""
        # Clear any existing data
        Bill.objects.all().delete()
        BillItem.objects.all().delete()
        
        patient_user = create_user_with_role('patient1', 'password', 'PATIENT')
        self.patient = PatientProfile.objects.create(user=patient_user)
        
        self.bill = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal('0.00')
        )
    
    def test_bill_item_creation(self):
        """Test creating a bill item"""
        item = BillItem.objects.create(
            bill=self.bill,
            description="Consultation Fee",
            quantity=1,
            unit_price=Decimal('50.00'),
            amount=Decimal('50.00')
        )
        
        self.assertEqual(BillItem.objects.count(), 1)
        self.assertEqual(item.description, "Consultation Fee")
        self.assertEqual(item.quantity, 1)
    
    def test_bill_item_string_representation(self):
        """Test bill item __str__ method"""
        item = BillItem.objects.create(
            bill=self.bill,
            description="X-Ray",
            quantity=2,
            unit_price=Decimal('25.00'),
            amount=Decimal('50.00')
        )
        
        self.assertEqual(str(item), "X-Ray (x2)")
    
    def test_bill_item_amount_calculation(self):
        """Test that amount is calculated from quantity * unit_price"""
        item = BillItem.objects.create(
            bill=self.bill,
            description="Lab Test",
            quantity=3,
            unit_price=Decimal('20.00')
        )
        
        # Amount should be auto-calculated
        self.assertEqual(item.amount, Decimal('60.00'))
    
    def test_bill_item_related_to_bill(self):
        """Test that bill items are related to bill"""
        BillItem.objects.create(
            bill=self.bill,
            description="Item 1",
            quantity=1,
            unit_price=Decimal('10.00')
        )
        BillItem.objects.create(
            bill=self.bill,
            description="Item 2",
            quantity=2,
            unit_price=Decimal('15.00')
        )
        
        self.assertEqual(self.bill.items.count(), 2)
    
    def test_bill_item_deletion_with_bill(self):
        """Test that bill items are deleted when bill is deleted"""
        BillItem.objects.create(
            bill=self.bill,
            description="Test Item",
            quantity=1,
            unit_price=Decimal('100.00')
        )
        
        self.assertEqual(BillItem.objects.count(), 1)
        
        # Delete the bill
        self.bill.delete()
        
        # Bill items should be deleted too (CASCADE)
        self.assertEqual(BillItem.objects.count(), 0)


class BillingIntegrationTest(TestCase):
    """Integration tests for billing system"""
    
    def setUp(self):
        """Set up test data"""
        self.patient_user = create_user_with_role('patient1', 'password', 'PATIENT')
        self.doctor_user = create_user_with_role('doctor1', 'password', 'DOCTOR')
        self.receptionist_user = create_user_with_role('receptionist1', 'password', 'RECEPTIONIST')
        
        self.patient = PatientProfile.objects.create(user=self.patient_user)
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            specialization='Cardiology'
        )
    
    def test_complete_billing_workflow(self):
        """Test complete billing workflow from creation to payment"""
        from datetime import time
        
        # 1. Create appointment
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(14, 30),
            reason="Heart checkup"
        )
        
        # 2. Create bill for appointment
        bill = Bill.objects.create(
            patient=self.patient,
            appointment=appointment,
            total_amount=Decimal('0.00'),
            status='Unpaid'
        )
        
        # 3. Add bill items
        items_data = [
            ("Consultation", 1, Decimal('100.00')),
            ("ECG Test", 1, Decimal('50.00')),
            ("Medication", 2, Decimal('25.00')),
        ]
        
        total = Decimal('0.00')
        for description, quantity, unit_price in items_data:
            item = BillItem.objects.create(
                bill=bill,
                description=description,
                quantity=quantity,
                unit_price=unit_price
            )
            total += item.amount
        
        # 4. Update bill total
        bill.total_amount = total
        bill.save()
        
        self.assertEqual(bill.total_amount, Decimal('200.00'))
        self.assertEqual(bill.items.count(), 3)
        
        # 5. Make partial payment
        bill.amount_paid = Decimal('100.00')
        bill.status = 'Partially Paid'
        bill.payment_method = 'Cash'
        bill.save()
        
        self.assertEqual(bill.amount_due, Decimal('100.00'))
        
        # 6. Complete payment
        bill.amount_paid = Decimal('200.00')
        bill.status = 'Paid'
        bill.save()
        
        self.assertEqual(bill.amount_due, Decimal('0.00'))
        self.assertEqual(bill.status, 'Paid')
    
    def test_bill_with_multiple_items_total(self):
        """Test that bill total matches sum of items"""
        bill = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal('0.00')
        )
        
        # Add various items
        BillItem.objects.create(
            bill=bill,
            description="Service 1",
            quantity=2,
            unit_price=Decimal('50.00')
        )
        BillItem.objects.create(
            bill=bill,
            description="Service 2",
            quantity=1,
            unit_price=Decimal('75.00')
        )
        BillItem.objects.create(
            bill=bill,
            description="Service 3",
            quantity=3,
            unit_price=Decimal('25.00')
        )
        
        # Calculate total from items
        total = sum(item.amount for item in bill.items.all())
        bill.total_amount = total
        bill.save()
        
        # Should be: (2*50) + (1*75) + (3*25) = 100 + 75 + 75 = 250
        self.assertEqual(bill.total_amount, Decimal('250.00'))
    
    def test_overdue_bill_detection(self):
        """Test detecting overdue bills"""
        # Create bill with past due date
        past_due_date = date.today() - timedelta(days=7)
        bill = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal('100.00'),
            amount_paid=Decimal('0.00'),
            status='Unpaid',
            due_date=past_due_date
        )
        
        # Check if bill is overdue
        is_overdue = bill.due_date < date.today() and bill.status != 'Paid'
        self.assertTrue(is_overdue)
    
    def test_patient_bill_history(self):
        """Test retrieving patient's billing history"""
        # Create multiple bills for patient
        for i in range(5):
            Bill.objects.create(
                patient=self.patient,
                total_amount=Decimal('100.00') * (i + 1),
                status='Paid' if i < 3 else 'Unpaid'
            )
        
        patient_bills = Bill.objects.filter(patient=self.patient)
        self.assertEqual(patient_bills.count(), 5)
        
        paid_bills = patient_bills.filter(status='Paid')
        unpaid_bills = patient_bills.filter(status='Unpaid')
        
        self.assertEqual(paid_bills.count(), 3)
        self.assertEqual(unpaid_bills.count(), 2)
    
    def test_mobile_money_payment(self):
        """Test mobile money payment methods"""
        bill = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal('50.00'),
            amount_paid=Decimal('50.00'),
            status='Paid',
            payment_method='MTN Mobile Money'
        )
        
        self.assertEqual(bill.payment_method, 'MTN Mobile Money')
        self.assertEqual(bill.status, 'Paid')
    
    def test_insurance_payment(self):
        """Test insurance payment method"""
        bill = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal('500.00'),
            amount_paid=Decimal('500.00'),
            status='Paid',
            payment_method='Insurance'
        )
        
        self.assertEqual(bill.payment_method, 'Insurance')


class BillingCalculationTest(TestCase):
    """Test suite for billing calculations and business logic"""
    
    def setUp(self):
        """Set up test data"""
        patient_user = create_user_with_role('patient1', 'password', 'PATIENT')
        self.patient = PatientProfile.objects.create(user=patient_user)
    
    def test_decimal_precision(self):
        """Test that decimal calculations maintain precision"""
        bill = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal('99.99'),
            amount_paid=Decimal('33.33')
        )
        
        self.assertEqual(bill.amount_due, Decimal('66.66'))
    
    def test_large_amounts(self):
        """Test handling large bill amounts"""
        bill = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal('9999999.99'),
            amount_paid=Decimal('5000000.00')
        )
        
        self.assertEqual(bill.amount_due, Decimal('4999999.99'))
    
    def test_zero_amount_bill(self):
        """Test bills with zero amount"""
        bill = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal('0.00'),
            amount_paid=Decimal('0.00'),
            status='Paid'
        )
        
        self.assertEqual(bill.amount_due, Decimal('0.00'))
    
    def test_bill_item_quantity_calculation(self):
        """Test various quantity calculations"""
        bill = Bill.objects.create(
            patient=self.patient,
            total_amount=Decimal('0.00')
        )
        
        # Test single item
        item1 = BillItem.objects.create(
            bill=bill,
            description="Single",
            quantity=1,
            unit_price=Decimal('10.50')
        )
        self.assertEqual(item1.amount, Decimal('10.50'))
        
        # Test multiple items
        item2 = BillItem.objects.create(
            bill=bill,
            description="Multiple",
            quantity=10,
            unit_price=Decimal('5.75')
        )
        self.assertEqual(item2.amount, Decimal('57.50'))
        
        # Test fractional price
        item3 = BillItem.objects.create(
            bill=bill,
            description="Fractional",
            quantity=3,
            unit_price=Decimal('12.33')
        )
        self.assertEqual(item3.amount, Decimal('36.99'))
