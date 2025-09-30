from django.urls import path
from . import views

app_name = 'prescriptions'

urlpatterns = [
    path('doctor/create/<int:patient_id>/', views.create_prescription_view, name='create_prescription'),
    path('doctor/<int:pk>/', views.prescription_detail_doctor_view, name='doctor_prescription_detail'),
    path('doctor/<int:pk>/status/', views.update_prescription_status_view, name='update_prescription_status'),
    path('patient/mine/', views.patient_prescription_list_view, name='patient_prescriptions'),
    path('patient/<int:pk>/', views.patient_prescription_detail_view, name='patient_prescription_detail'),
    path('download/<int:pk>/', views.prescription_download_view, name='prescription_download'),
    path('batch/download/', views.prescription_batch_download_view, name='prescription_batch_download'),
]
