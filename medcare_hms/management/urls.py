from django.urls import path
from . import views

urlpatterns = [
    # Department URLs
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/add/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/update/', views.DepartmentUpdateView.as_view(), name='department_update'),
    path('departments/<int:pk>/toggle/', views.department_toggle_active, name='department_toggle_active'),

    # Room URLs
    path('rooms/', views.RoomListView.as_view(), name='room_list'),
    path('rooms/add/', views.RoomCreateView.as_view(), name='room_create'),
    path('rooms/<int:pk>/update/', views.RoomUpdateView.as_view(), name='room_update'),
    path('rooms/<int:pk>/toggle/', views.room_toggle_active, name='room_toggle_active'),
    
    # Staff URLs
    path('doctors/', views.DoctorListView.as_view(), name='doctor_list'),
    path('receptionists/', views.ReceptionistListView.as_view(), name='receptionist_list'),
]