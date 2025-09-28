import django_filters
from patients.models import Appointment

class AppointmentFilter(django_filters.FilterSet):
    # Add filters for date ranges
    start_date = django_filters.DateFilter(field_name='appointment_date', lookup_expr='gte', label='From Date')
    end_date = django_filters.DateFilter(field_name='appointment_date', lookup_expr='lte', label='To Date')

    class Meta:
        model = Appointment
        # Define fields to filter by directly
        fields = {
            'doctor': ['exact'],
            'status': ['exact'],
        }