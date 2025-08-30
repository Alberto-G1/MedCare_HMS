# medcare_hms/billing/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.BillListView.as_view(), name='bill_list'),
    path('generate/', views.select_appointment_for_billing, name='select_appointment_for_billing'),
    path('generate/<int:appointment_id>/', views.create_bill_for_appointment, name='create_bill_for_appointment'),
    path('update-status/<int:bill_id>/', views.update_bill_status, name='update_bill_status'),
]