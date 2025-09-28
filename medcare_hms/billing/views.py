# billing/views.py (FINAL VERSION)

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Sum, Q, Count, DecimalField
from decimal import Decimal, InvalidOperation
from patients.models import Appointment, PatientProfile
from .models import Bill, BillItem
from .forms import BillForm, BillItemForm, UpdatePaymentForm
from accounts.decorators import receptionist_required
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import date
from django.urls import reverse
from notifications.utils import create_notification 
from .filters import BillFilter

staff_decorators = [login_required, receptionist_required]

@method_decorator(staff_decorators, name='dispatch')
class BillListView(ListView):
    model = Bill
    template_name = 'billing/bill_list.html'
    context_object_name = 'bills'
    
    def get_queryset(self):
        """
        This method now handles the filtering directly.
        """
        # Start with the base queryset
        queryset = Bill.objects.select_related('patient__user', 'patient__user__patientprofile').order_by('-bill_date')
        
        # Apply the django-filter FilterSet
        self.filterset = BillFilter(self.request.GET, queryset=queryset)
        
        # Return the filtered queryset
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        """
        This method adds the filter form and statistics to the context.
        """
        context = super().get_context_data(**kwargs)
        today = date.today()
        
        # Add the filter form to the context
        context['filter'] = self.filterset
        context['bills'] = self.filterset.qs
        
        # # Aggregate statistics for the dashboard cards
        paid_stats = Bill.objects.filter(status='Paid').aggregate(count=Count('id'), total=Coalesce(Sum('total_amount'), 0, output_field=DecimalField()))
        unpaid_stats = Bill.objects.filter(status='Unpaid').aggregate(count=Count('id'), total=Coalesce(Sum('total_amount'), 0, output_field=DecimalField()))
        partially_paid_stats = Bill.objects.filter(status='Partially Paid').aggregate(count=Count('id'), total=Coalesce(Sum('amount_paid'), 0, output_field=DecimalField())) # Sum amount_paid for this card
        overdue_stats = Bill.objects.filter(status='Unpaid', due_date__lt=today).aggregate(count=Count('id'), total=Coalesce(Sum('total_amount'), 0, output_field=DecimalField()))
        
        context['paid_bills_count'] = paid_stats['count']
        context['paid_bills_total'] = paid_stats['total']
        context['unpaid_bills_count'] = unpaid_stats['count']
        context['unpaid_bills_total'] = unpaid_stats['total']
        context['partially_paid_bills_count'] = partially_paid_stats['count']
        context['partially_paid_bills_total'] = partially_paid_stats['total']
        context['overdue_bills_count'] = overdue_stats['count']
        context['overdue_bills_total'] = overdue_stats['total']
        
        return context
    
        # context = super().get_context_data(**kwargs)
        # today = date.today()
        
        # # Apply the filter to the queryset
        # bill_filter = BillFilter(self.request.GET, queryset=self.get_queryset())
        # context['filter'] = bill_filter
        # context['bills'] = bill_filter.qs
        # # Aggregate statistics for the dashboard cards
        # paid_stats = Bill.objects.filter(status='Paid').aggregate(count=Count('id'), total=Coalesce(Sum('total_amount'), 0, output_field=DecimalField()))
        # unpaid_stats = Bill.objects.filter(status='Unpaid').aggregate(count=Count('id'), total=Coalesce(Sum('total_amount'), 0, output_field=DecimalField()))
        # partially_paid_stats = Bill.objects.filter(status='Partially Paid').aggregate(count=Count('id'), total=Coalesce(Sum('amount_paid'), 0, output_field=DecimalField())) # Sum amount_paid for this card
        # overdue_stats = Bill.objects.filter(status='Unpaid', due_date__lt=today).aggregate(count=Count('id'), total=Coalesce(Sum('total_amount'), 0, output_field=DecimalField()))
        
        # context['paid_bills_count'] = paid_stats['count']
        # context['paid_bills_total'] = paid_stats['total']
        # context['unpaid_bills_count'] = unpaid_stats['count']
        # context['unpaid_bills_total'] = unpaid_stats['total']
        # context['partially_paid_bills_count'] = partially_paid_stats['count']
        # context['partially_paid_bills_total'] = partially_paid_stats['total']
        # context['overdue_bills_count'] = overdue_stats['count']
        # context['overdue_bills_total'] = overdue_stats['total']
        
        # # THE INCORRECT LINE HAS BEEN REMOVED FROM HERE
        
        # return context

@method_decorator(staff_decorators, name='dispatch')
class BillDetailView(DetailView):
    model = Bill
    template_name = 'billing/bill_detail.html'
    context_object_name = 'bill'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['item_form'] = BillItemForm() # Pass the form for adding new items
        context['item_form'] = BillItemForm()
        context['payment_form'] = UpdatePaymentForm(instance=self.object)
        return context

@login_required
@receptionist_required
def create_bill_view(request):
    if request.method == 'POST':
        form = BillForm(request.POST)
        if form.is_valid():
            bill = form.save()

            # --- NOTIFICATION LOGIC ---
            patient_user = bill.patient.user
            message = f"A new miscellaneous bill (ID: #{bill.pk}) has been generated for you."
            create_notification(recipient=patient_user, message=message, link=reverse('patients:my_bills_list'))
            # --- END NOTIFICATION LOGIC ---

            messages.success(request, f"New bill created for {bill.patient.user.username}. You can now add items.")
            return redirect('billing:bill_detail', pk=bill.pk)
    else:
        form = BillForm()
    
    context = {'form': form}
    return render(request, 'billing/create_bill.html', context)

@login_required
@receptionist_required
def add_bill_item_view(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id)
    if request.method == 'POST':
        form = BillItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.bill = bill
            item.save()
            
            # Recalculate the bill's total amount
            total = bill.items.aggregate(total=Sum('amount'))['total'] or 0.00
            bill.total_amount = total
            bill.save()

            messages.success(request, f"Item '{item.description}' added to Bill #{bill.pk}.")
    return redirect('billing:bill_detail', pk=bill.pk)

@login_required
@receptionist_required
def update_payment_status_view(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id)
    if request.method == 'POST':
        form = UpdatePaymentForm(request.POST, instance=bill) # Not used, but good practice
        
        new_status = request.POST.get('status')
        new_payment_str = request.POST.get('new_payment_amount', '0')
        
        try:
            # --- THIS IS THE FIX: Convert the input to a Decimal ---
            new_payment = Decimal(new_payment_str if new_payment_str else '0.00')
        except InvalidOperation:
            messages.error(request, "Invalid payment amount entered.")
            return redirect('billing:bill_detail', pk=bill.pk)

        if new_status == 'Paid':
            bill.amount_paid = bill.total_amount
            bill.status = 'Paid'
            messages.success(request, f"Bill #{bill.id} has been marked as Fully Paid.")
        
        elif new_status == 'Partially Paid':
            if new_payment <= 0:
                messages.error(request, "Please enter a payment amount greater than zero for a partial payment.")
                return redirect('billing:bill_detail', pk=bill.pk)
            
            bill.amount_paid += new_payment
            
            if bill.amount_paid >= bill.total_amount:
                bill.amount_paid = bill.total_amount
                bill.status = 'Paid'
                messages.success(request, f"Final payment of {new_payment:,.2f} received. Bill #{bill.id} is now Fully Paid.")
            else:
                bill.status = 'Partially Paid'
                messages.info(request, f"Partial payment of UGX {new_payment:,.0f} recorded for Bill #{bill.id}.")

        elif new_status == 'Unpaid':
            bill.amount_paid = Decimal('0.00') # Use a Decimal for consistency
            bill.status = 'Unpaid'
            messages.warning(request, f"Bill #{bill.id} status has been reset to Unpaid.")
        
        # Only update payment_method if it was provided in the form
        payment_method = request.POST.get('payment_method')
        if payment_method:
            bill.payment_method = payment_method
        
        bill.save()

    return redirect('billing:bill_detail', pk=bill.pk)

@method_decorator(staff_decorators, name='dispatch')
class BillReceiptView(DetailView):
    model = Bill
    template_name = 'billing/bill_receipt.html'
    context_object_name = 'bill'


@login_required
@receptionist_required
def select_appointment_for_billing(request):
    """
    Step 1: Display a list of completed appointments that don't have a bill yet.
    """
    # Get IDs of appointments that already have a bill
    billed_appointment_ids = Bill.objects.exclude(appointment__isnull=True).values_list('appointment_id', flat=True)
    
    # Find appointments that are 'Completed' and are not yet billed
    unbilled_appointments = Appointment.objects.filter(status='Completed').exclude(id__in=billed_appointment_ids)
    
    context = {
        'appointments': unbilled_appointments
    }
    return render(request, 'billing/select_appointment.html', context)

@login_required
@receptionist_required
def create_bill_from_appointment(request, appointment_id):
    """
    Step 2: Automatically create a bill linked to the selected appointment and patient.
    """
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    
    # Check if a bill already exists for this appointment to prevent duplicates
    if Bill.objects.filter(appointment=appointment).exists():
        messages.error(request, "A bill already exists for this appointment.")
        return redirect('billing:select_appointment')

    # Automatically create the bill
    bill = Bill.objects.create(
        patient=appointment.patient,
        appointment=appointment
    )
    
    # Optional: Pre-populate with a consultation fee
    BillItem.objects.create(
        bill=bill,
        description=f"Consultation with {appointment.doctor}",
        quantity=1,
        unit_price=50000 # Example price in UGX
    )
    
    # Recalculate total
    total = bill.items.aggregate(total=Sum('amount'))['total'] or 0.00
    bill.total_amount = total
    bill.save()

    # --- NOTIFICATION LOGIC ---
    patient_user = bill.patient.user
    message = f"A new bill (ID: #{bill.pk}) has been generated for you."
    create_notification(recipient=patient_user, message=message, link=reverse('patients:my_bills_list'))
    # --- END NOTIFICATION LOGIC ---

    messages.success(request, "Bill created successfully. You can now add more items.")
    return redirect('billing:bill_detail', pk=bill.pk)

@login_required
@receptionist_required
def edit_bill_item_view(request, pk):
    item = get_object_or_404(BillItem, pk=pk)
    bill = item.bill
    
    # Prevent editing of the initial consultation fee
    if "Consultation with" in item.description:
        messages.error(request, "The primary consultation fee cannot be edited.")
        return redirect('billing:bill_detail', pk=bill.pk)

    if request.method == 'POST':
        form = BillItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            # Recalculate total
            total = bill.items.aggregate(total=Sum('amount'))['total'] or 0.00
            bill.total_amount = total
            bill.save()
            messages.success(request, "Bill item updated successfully.")
            return redirect('billing:bill_detail', pk=bill.pk)
    else:
        form = BillItemForm(instance=item)
    
    return render(request, 'billing/edit_bill_item.html', {'form': form, 'item': item})

@login_required
@receptionist_required
def delete_bill_item_view(request, pk):
    item = get_object_or_404(BillItem, pk=pk)
    bill = item.bill

    # Prevent deleting of the initial consultation fee
    if "Consultation with" in item.description:
        messages.error(request, "The primary consultation fee cannot be deleted.")
        return redirect('billing:bill_detail', pk=bill.pk)

    if request.method == 'POST':
        item.delete()
        # Recalculate total
        total = bill.items.aggregate(total=Sum('amount'))['total'] or 0.00
        bill.total_amount = total
        bill.save()
        messages.success(request, "Bill item deleted successfully.")
        return redirect('billing:bill_detail', pk=bill.pk)

    return render(request, 'billing/delete_bill_item_confirm.html', {'item': item})

@login_required
@receptionist_required
def delete_bill_view(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if request.method == 'POST':
        patient_name = bill.patient.user.get_full_name
        bill.delete()
        messages.success(request, f"Bill #{pk} for {patient_name} has been successfully deleted.")
        return redirect('billing:bill_list')
    
    return render(request, 'billing/delete_bill_confirm.html', {'bill': bill})