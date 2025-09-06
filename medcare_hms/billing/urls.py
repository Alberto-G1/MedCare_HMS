# billing/urls.py

from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.BillListView.as_view(), name='bill_list'),
    path('create/', views.create_bill_view, name='create_bill'),
    path('<int:pk>/', views.BillDetailView.as_view(), name='bill_detail'),
    path('<int:bill_id>/add-item/', views.add_bill_item_view, name='add_bill_item'),
    path('<int:bill_id>/update-status/', views.update_bill_status, name='update_bill_status'),
]