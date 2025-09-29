import django_filters
from django.db.models import Q
from patients.models import Appointment


class AppointmentFilter(django_filters.FilterSet):
    """
    Enhanced Appointment filter:
    - Date range (start_date / end_date)
    - Doctor (exact)
    - Status (exact)
    - Patient name (partial across first / last / username)
    - Reason (icontains)
    """
    start_date = django_filters.DateFilter(field_name='appointment_date', lookup_expr='gte', label='From Date')
    end_date = django_filters.DateFilter(field_name='appointment_date', lookup_expr='lte', label='To Date')
    patient = django_filters.CharFilter(method='filter_patient', label='Patient Name')
    reason = django_filters.CharFilter(field_name='reason', lookup_expr='icontains', label='Reason Contains')

    def filter_patient(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(patient__user__first_name__icontains=value) |
            Q(patient__user__last_name__icontains=value) |
            Q(patient__user__username__icontains=value)
        )

    class Meta:
        model = Appointment
        fields = ['doctor', 'status', 'patient', 'reason']