# reports/views.py (CORRECTED)

import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.decorators import admin_required
# --- ADD F to the import list ---
from django.db.models import Count, Sum, F, DecimalField
from django.db.models.functions import TruncMonth, Coalesce
from patients.models import Appointment
from billing.models import Bill

@login_required
@admin_required
def reports_dashboard_view(request):
    # --- 1. KPI Cards Data ---
    total_appointments = Appointment.objects.count()
    completed_appointments = Appointment.objects.filter(status='Completed').count()
    
    total_revenue = Bill.objects.filter(status='Paid').aggregate(
        total=Coalesce(Sum('total_amount'), 0, output_field=DecimalField())
    )['total']
    
    # --- THIS IS THE FIX ---
    # We are telling the database: "For each row, calculate (total_amount - amount_paid),
    # then sum up all of those results."
    outstanding_revenue = Bill.objects.filter(status__in=['Unpaid', 'Partially Paid']).aggregate(
        total=Coalesce(Sum(F('total_amount') - F('amount_paid')), 0, output_field=DecimalField())
    )['total']
    # --- END OF FIX ---
    
    # --- 2. Appointments per Month Chart Data ---
    # ... (This part is correct and remains the same) ...
    appointments_by_month = Appointment.objects.annotate(month=TruncMonth('appointment_date')).values('month').annotate(count=Count('id')).order_by('month')
    appt_month_labels = [d['month'].strftime('%b %Y') for d in appointments_by_month]
    appt_month_data = [d['count'] for d in appointments_by_month]

    # --- 3. Revenue per Month Chart Data ---
    # ... (This part is correct and remains the same) ...
    revenue_by_month = Bill.objects.filter(status='Paid').annotate(month=TruncMonth('bill_date')).values('month').annotate(total=Sum('total_amount')).order_by('month')
    rev_month_labels = [r['month'].strftime('%b %Y') for r in revenue_by_month]
    rev_month_data = [float(r['total']) for r in revenue_by_month]

    context = {
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'total_revenue': total_revenue,
        'outstanding_revenue': outstanding_revenue,
        
        'appt_month_labels': json.dumps(appt_month_labels),
        'appt_month_data': json.dumps(appt_month_data),
        'rev_month_labels': json.dumps(rev_month_labels),
        'rev_month_data': json.dumps(rev_month_data),
    }
    return render(request, 'reports/reports_dashboard.html', context)