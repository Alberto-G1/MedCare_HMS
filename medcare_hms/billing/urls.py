from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Main list of all bills
    path('', views.BillListView.as_view(), name='bill_list'),
    
    # --- PRIMARY WORKFLOW: Create bill from a completed appointment ---
    path('from-appointment/', views.select_appointment_for_billing, name='select_appointment'),
    path('from-appointment/<int:appointment_id>/create/', views.create_bill_from_appointment, name='create_bill_from_appointment'),
    
    # --- SECONDARY WORKFLOW: Create a miscellaneous bill (e.g., for supplies) ---
    path('create-misc/', views.create_bill_view, name='create_misc_bill'),
    
    # --- Bill Management ---
    path('<int:pk>/', views.BillDetailView.as_view(), name='bill_detail'),
    path('<int:bill_id>/add-item/', views.add_bill_item_view, name='add_bill_item'),
    path('<int:bill_id>/update-status/', views.update_payment_status_view, name='update_bill_status'),
    path('<int:pk>/receipt/', views.BillReceiptView.as_view(), name='bill_receipt'),

    # --- URLS FOR ITEM EDIT/DELETE ---
    path('item/<int:pk>/edit/', views.edit_bill_item_view, name='edit_bill_item'),
    path('item/<int:pk>/delete/', views.delete_bill_item_view, name='delete_bill_item'),
    path('<int:pk>/delete/', views.delete_bill_view, name='delete_bill'),

]