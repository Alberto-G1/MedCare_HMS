from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Sum

# Import from the correct apps
from patients.models import Appointment
from .models import Bill, BillItem
from .forms import BillForm, BillItemForm # <-- IMPORT THE NEW, CORRECT FORMS
from accounts.decorators import receptionist_required, admin_required

# Helper decorator for DRY code
staff_decorators = [login_required, receptionist_required]

@method_decorator(staff_decorators, name='dispatch')
class BillListView(ListView):
    model = Bill
    template_name = 'billing/bill_list.html'
    context_object_name = 'bills'
    # Use select_related for performance optimization
    queryset = Bill.objects.select_related('patient__user').order_by('-bill_date')

@method_decorator(staff_decorators, name='dispatch')
class BillDetailView(DetailView):
    model = Bill
    template_name = 'billing/bill_detail.html'
    context_object_name = 'bill'

@login_required
@receptionist_required
@admin_required
def create_bill_view(request):
    """
    View to create a new bill for a patient.
    Can be optionally linked to a completed appointment.
    """
    if request.method == 'POST':
        form = BillForm(request.POST)
        if form.is_valid():
            bill = form.save()
            messages.success(request, f"New bill created for {bill.patient.user.username}. You can now add items.")
            # Redirect to the detail view to add items
            return redirect('billing:bill_detail', pk=bill.pk)
    else:
        form = BillForm()
    
    context = {'form': form}
    return render(request, 'billing/create_bill.html', context)


@login_required
@receptionist_required
@admin_required
def add_bill_item_view(request, bill_id):
    """
    View to add a new line item to an existing bill.
    """
    bill = get_object_or_404(Bill, pk=bill_id)
    if request.method == 'POST':
        form = BillItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.bill = bill
            item.save() # The amount is calculated automatically in the model's save method
            
            # --- Recalculate the bill's total amount ---
            total = bill.items.aggregate(total=Sum('amount'))['total'] or 0.00
            bill.total_amount = total
            bill.save()

            messages.success(request, f"Item '{item.description}' added to Bill #{bill.pk}.")
            return redirect('billing:bill_detail', pk=bill.pk)
    else:
        form = BillItemForm()

    context = {
        'form': form,
        'bill': bill
    }
    return render(request, 'billing/add_bill_item.html', context)


@login_required
@receptionist_required
@admin_required
def update_bill_status(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id)
    # This is a simple toggle. In a real app, you'd have a form to select status and payment method.
    if bill.status == 'Unpaid':
        bill.status = 'Paid'
        messages.success(request, f"Bill #{bill.id} has been marked as Paid.")
    else:
        bill.status = 'Unpaid'
        messages.info(request, f"Bill #{bill.id} has been marked as Unpaid.")
    bill.save()
    return redirect('billing:bill_list')