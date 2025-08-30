# medcare_hms/billing/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from patients.models import Appointment, Bill
from .forms import BillGenerationForm
from accounts.decorators import receptionist_required, admin_required

@method_decorator(login_required, name='dispatch')
@method_decorator(receptionist_required, name='dispatch')
class BillListView(ListView):
    model = Bill
    template_name = 'billing/bill_list.html'
    context_object_name = 'bills'
    queryset = Bill.objects.select_related('appointment', 'appointment__patient__user', 'appointment__doctor__user').order_by('-appointment__appointment_date')

@login_required
@receptionist_required
def select_appointment_for_billing(request):
    # Find completed appointments that do not have a bill yet
    billed_appointment_ids = Bill.objects.values_list('appointment_id', flat=True)
    unbilled_appointments = Appointment.objects.filter(status='Completed').exclude(id__in=billed_appointment_ids)
    
    context = {
        'appointments': unbilled_appointments
    }
    return render(request, 'billing/select_appointment.html', context)


@login_required
@receptionist_required
def create_bill_for_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    
    if request.method == 'POST':
        form = BillGenerationForm(request.POST)
        if form.is_valid():
            bill = form.save(commit=False)
            bill.appointment = appointment
            bill.save()
            messages.success(request, f"Bill for appointment on {appointment.appointment_date} has been created.")
            return redirect('bill_list')
    else:
        form = BillGenerationForm()

    context = {
        'form': form,
        'appointment': appointment
    }
    return render(request, 'billing/generate_bill_form.html', context)


@login_required
@receptionist_required
def update_bill_status(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id)
    if bill.payment_status == 'Unpaid':
        bill.payment_status = 'Paid'
        messages.success(request, f"Bill #{bill.id} has been marked as Paid.")
    else:
        bill.payment_status = 'Unpaid'
        messages.info(request, f"Bill #{bill.id} has been marked as Unpaid.")
    bill.save()
    return redirect('bill_list')