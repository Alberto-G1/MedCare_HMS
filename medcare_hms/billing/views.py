# billing/views.py (FINAL VERSION)

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Sum, Q

from patients.models import Appointment, PatientProfile
from .models import Bill, BillItem
from .forms import BillForm, BillItemForm
from accounts.decorators import receptionist_required

staff_decorators = [login_required, receptionist_required]

@method_decorator(staff_decorators, name='dispatch')
class BillListView(ListView):
    model = Bill
    template_name = 'billing/bill_list.html'
    context_object_name = 'bills'
    
    def get_queryset(self):
        queryset = Bill.objects.select_related('patient__user').order_by('-bill_date')
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(patient__user__first_name__icontains=query) |
                Q(patient__user__last_name__icontains=query) |
                Q(patient__user__username__icontains=query) |
                Q(pk__icontains=query)
            )
        return queryset

@method_decorator(staff_decorators, name='dispatch')
class BillDetailView(DetailView):
    model = Bill
    template_name = 'billing/bill_detail.html'
    context_object_name = 'bill'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['item_form'] = BillItemForm() # Pass the form for adding new items
        return context

@login_required
@receptionist_required
def create_bill_view(request):
    if request.method == 'POST':
        form = BillForm(request.POST)
        if form.is_valid():
            bill = form.save()
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
        new_status = request.POST.get('status')
        if new_status in ['Paid', 'Unpaid', 'Partially Paid']:
            bill.status = new_status
            bill.save()
            messages.success(request, f"Bill #{bill.id} status updated to {new_status}.")
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

    messages.success(request, "Bill created successfully. You can now add more items.")
    return redirect('billing:bill_detail', pk=bill.pk)