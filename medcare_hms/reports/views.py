# reports/views.py (CORRECTED)

import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.decorators import admin_required
from django.db.models import Count, Sum, F, DecimalField
from django.db.models.functions import TruncMonth, Coalesce
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from patients.models import Appointment, PatientProfile
from billing.models import Bill
from prescriptions.models import Prescription

@login_required
@admin_required
def reports_dashboard_view(request):
    """Render dashboard shell; primary data loaded via AJAX JSON endpoints."""
    # Provide minimal initial counts (optional fast render) or placeholders
    return render(request, 'reports/reports_dashboard.html')


@login_required
@admin_required
def kpi_summary_api(request):
    """Return JSON for KPI cards."""
    total_appointments = Appointment.objects.count()
    completed_appointments = Appointment.objects.filter(status='Completed').count()
    cancelled_appointments = Appointment.objects.filter(status__in=['Cancelled','Rejected']).count()
    active_prescriptions = Prescription.objects.filter(status='ACTIVE').count()

    # New patients in last 30 days (based on related user date_joined)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_patients = PatientProfile.objects.filter(user__date_joined__gte=thirty_days_ago).count()

    total_revenue = Bill.objects.filter(status='Paid').aggregate(
        total=Coalesce(Sum('total_amount'), 0, output_field=DecimalField())
    )['total']
    outstanding_revenue = Bill.objects.filter(status__in=['Unpaid', 'Partially Paid']).aggregate(
        total=Coalesce(Sum(F('total_amount') - F('amount_paid')), 0, output_field=DecimalField())
    )['total']

    return JsonResponse({
        'totalAppointments': total_appointments,
        'completedAppointments': completed_appointments,
        'cancelledAppointments': cancelled_appointments,
        'activePrescriptions': active_prescriptions,
        'newPatients30Days': new_patients,
        'totalRevenue': float(total_revenue),
        'outstandingRevenue': float(outstanding_revenue),
    })


@login_required
@admin_required
def appointments_over_time_api(request):
    appointments_by_month = (
        Appointment.objects
        .annotate(month=TruncMonth('appointment_date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    labels = [d['month'].strftime('%b %Y') for d in appointments_by_month]
    data = [d['count'] for d in appointments_by_month]
    return JsonResponse({'labels': labels, 'data': data})


@login_required
@admin_required
def revenue_over_time_api(request):
    revenue_by_month = (
        Bill.objects.filter(status='Paid')
        .annotate(month=TruncMonth('bill_date'))
        .values('month')
        .annotate(total=Sum('total_amount'))
        .order_by('month')
    )
    labels = [r['month'].strftime('%b %Y') for r in revenue_by_month]
    data = [float(r['total']) for r in revenue_by_month]
    return JsonResponse({'labels': labels, 'data': data})


@login_required
@admin_required
def revenue_by_doctor_api(request):
    """Aggregate paid revenue by doctor (through appointment -> doctor)"""
    # Only consider bills linked to appointments & paid
    qs = (
        Bill.objects.filter(status='Paid', appointment__doctor__isnull=False)
        .values('appointment__doctor__user__first_name', 'appointment__doctor__user__last_name')
        .annotate(total=Sum('total_amount'))
        .order_by('-total')[:10]
    )
    labels = [
        (row['appointment__doctor__user__first_name'] or row['appointment__doctor__user__last_name'] or 'Doctor')
        for row in qs
    ]
    data = [float(row['total']) for row in qs]
    return JsonResponse({'labels': labels, 'data': data})


@login_required
@admin_required
def prescriptions_activity_api(request):
    """Return counts of prescriptions by status for a simple donut chart."""
    status_counts = (
        Prescription.objects.values('status').annotate(count=Count('id'))
    )
    mapping = {'ACTIVE': 'Active', 'COMPLETED': 'Completed', 'CANCELLED': 'Cancelled'}
    labels = [mapping.get(r['status'], r['status']) for r in status_counts]
    data = [r['count'] for r in status_counts]
    return JsonResponse({'labels': labels, 'data': data})