import django_filters
from django.db.models import Q
from .models import Bill


class BillFilter(django_filters.FilterSet):
    """Enhanced bill filter with date range, patient name, amount range, status, payment method."""
    start_date = django_filters.DateFilter(field_name='bill_date', lookup_expr='gte', label='From Date')
    end_date = django_filters.DateFilter(field_name='bill_date', lookup_expr='lte', label='To Date')
    patient = django_filters.CharFilter(method='filter_patient', label='Patient Name')
    min_total = django_filters.NumberFilter(field_name='total_amount', lookup_expr='gte', label='Min Total')
    max_total = django_filters.NumberFilter(field_name='total_amount', lookup_expr='lte', label='Max Total')
    payment_method = django_filters.CharFilter(field_name='payment_method', lookup_expr='iexact', label='Payment Method')

    def filter_patient(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(patient__user__first_name__icontains=value) |
            Q(patient__user__last_name__icontains=value) |
            Q(patient__user__username__icontains=value)
        )

    class Meta:
        model = Bill
        fields = ['status', 'patient', 'payment_method', 'min_total', 'max_total']