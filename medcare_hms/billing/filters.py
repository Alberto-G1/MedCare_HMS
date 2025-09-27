import django_filters
from .models import Bill

class BillFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='bill_date', lookup_expr='gte', label='From Date')
    end_date = django_filters.DateFilter(field_name='bill_date', lookup_expr='lte', label='To Date')

    class Meta:
        model = Bill
        fields = ['status']