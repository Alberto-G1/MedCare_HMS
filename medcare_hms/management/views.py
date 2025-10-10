from django.shortcuts import render, redirect, get_object_or_404 
from django.contrib import messages
from .forms import DepartmentForm, RoomForm
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin 
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
from accounts.decorators import admin_required
from .models import Department, Room

@method_decorator(admin_required, name='dispatch')
class DepartmentListView(ListView):
    model = Department
    template_name = 'management/department_list.html'
    context_object_name = 'departments'
    # By default, order by name and show active ones first
    queryset = Department.objects.all().order_by('-is_active', 'name')

@method_decorator(admin_required, name='dispatch')
class DepartmentCreateView(SuccessMessageMixin, CreateView):
    model = Department
    form_class = DepartmentForm # <-- USE OUR CUSTOM FORM
    template_name = 'management/department_form.html'
    success_url = reverse_lazy('management:department_list')
    success_message = "Department '%(name)s' was created successfully."

@method_decorator(admin_required, name='dispatch')
class DepartmentUpdateView(SuccessMessageMixin, UpdateView):
    model = Department
    form_class = DepartmentForm # <-- USE OUR CUSTOM FORM
    template_name = 'management/department_form.html'
    success_url = reverse_lazy('management:department_list')
    success_message = "Department '%(name)s' was updated successfully."

@admin_required
def department_toggle_active(request, pk):
    department = get_object_or_404(Department, pk=pk)
    
    # Logic to prevent deactivating the last active department
    if department.is_active:
        if Department.objects.filter(is_active=True).count() == 1:
            messages.error(request, "Cannot deactivate the last active department.")
            return redirect('management:department_list')
    
    department.is_active = not department.is_active
    department.save()
    
    if department.is_active:
        messages.success(request, f"Department '{department.name}' has been activated.")
    else:
        messages.info(request, f"Department '{department.name}' has been deactivated.")
        
    return redirect('management:department_list')

# --- Room Views ---

@method_decorator(admin_required, name='dispatch')
class RoomListView(ListView):
    model = Room
    template_name = 'management/room_list.html'
    context_object_name = 'rooms'
    queryset = Room.objects.select_related('department').order_by('department__name', 'room_number')

@method_decorator(admin_required, name='dispatch')
class RoomCreateView(SuccessMessageMixin, CreateView):
    model = Room
    form_class = RoomForm # <-- USE OUR CUSTOM FORM
    template_name = 'management/room_form.html'
    success_url = reverse_lazy('management:room_list')
    success_message = "Room '%(room_number)s' in department '%(department)s' was created successfully."

@method_decorator(admin_required, name='dispatch')
class RoomUpdateView(SuccessMessageMixin, UpdateView):
    model = Room
    form_class = RoomForm # <-- USE OUR CUSTOM FORM
    template_name = 'management/room_form.html'
    success_url = reverse_lazy('management:room_list')
    success_message = "Room '%(room_number)s' was updated successfully."

@admin_required
def room_toggle_active(request, pk):
    room = get_object_or_404(Room, pk=pk)
    
    # Placeholder for checking occupancy before deactivating
    # from admissions.models import Admission
    # active_admissions = Admission.objects.filter(room=room, is_discharged=False).exists()
    active_admissions = False # Placeholder value
    
    if room.is_active and active_admissions:
        messages.error(request, f"Cannot deactivate Room {room.room_number}. It is currently occupied.")
        return redirect('management:room_list')
        
    room.is_active = not room.is_active
    room.save()
    
    if room.is_active:
        messages.success(request, f"Room '{room.room_number}' has been activated.")
    else:
        messages.info(request, f"Room '{room.room_number}' has been deactivated.")
        
    return redirect('management:room_list')