from django.shortcuts import render, redirect, get_object_or_404 
from django.contrib import messages
from .forms import DepartmentForm, RoomForm
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin 
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
from accounts.decorators import admin_required
from .models import Department, Room
from django.http import JsonResponse
from doctors.models import DoctorProfile
from receptionist.models import ReceptionistProfile
from django.db.models import Q

@method_decorator(admin_required, name='dispatch')
class DepartmentListView(ListView):
    model = Department
    template_name = 'management/department_list.html'
    context_object_name = 'departments'
    # By default, order by name and show active ones first
    queryset = Department.objects.all().order_by('-is_active', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        departments = context['departments']
        context['total_count'] = departments.count()
        context['active_count'] = departments.filter(is_active=True).count()
        context['inactive_count'] = departments.filter(is_active=False).count()
        return context

@method_decorator(admin_required, name='dispatch')
class DepartmentCreateView(SuccessMessageMixin, CreateView):
    model = Department
    form_class = DepartmentForm # <-- USE OUR CUSTOM FORM
    template_name = 'management/department_form.html'
    success_url = reverse_lazy('management:department_list')
    success_message = "Department '%(name)s' was created successfully."
    
    def form_valid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request
            department = form.save()
            return JsonResponse({
                'success': True,
                'message': f"Department '{department.name}' was created successfully.",
                'department_id': department.pk
            })
        else:
            # Regular form submission
            return super().form_valid(form)
    
    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            return JsonResponse({
                'success': False,
                'errors': errors
            })
        else:
            # Regular form submission
            return super().form_invalid(form)

@method_decorator(admin_required, name='dispatch')
class DepartmentUpdateView(SuccessMessageMixin, UpdateView):
    model = Department
    form_class = DepartmentForm # <-- USE OUR CUSTOM FORM
    template_name = 'management/department_form.html'
    success_url = reverse_lazy('management:department_list')
    
    def form_valid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request
            department = form.save()
            return JsonResponse({
                'success': True,
                'message': f"Department '{department.name}' was updated successfully.",
                'department_id': department.pk
            })
        else:
            # Regular form submission
            messages.success(self.request, f"Department '{form.instance.name}' was updated successfully.")
            return super().form_valid(form)
    
    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            return JsonResponse({
                'success': False,
                'errors': errors
            })
        else:
            # Regular form submission
            return super().form_invalid(form)
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rooms = context['rooms']
        context['total_count'] = rooms.count()
        context['available_count'] = rooms.filter(status='AVAILABLE').count()
        context['occupied_count'] = rooms.filter(status='OCCUPIED').count()
        context['maintenance_count'] = rooms.filter(status='MAINTENANCE').count()
        context['active_count'] = rooms.filter(is_active=True).count()
        context['active_departments'] = Department.objects.filter(is_active=True).order_by('name')
        return context

@method_decorator(admin_required, name='dispatch')
class RoomCreateView(SuccessMessageMixin, CreateView):
    model = Room
    form_class = RoomForm # <-- USE OUR CUSTOM FORM
    template_name = 'management/room_form.html'
    success_url = reverse_lazy('management:room_list')
    success_message = "Room '%(room_number)s' in department '%(department)s' was created successfully."
    
    def form_valid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request
            room = form.save()
            return JsonResponse({
                'success': True,
                'message': f"Room '{room.room_number}' in department '{room.department.name}' was created successfully.",
                'room_id': room.pk
            })
        else:
            # Regular form submission
            return super().form_valid(form)
    
    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            return JsonResponse({
                'success': False,
                'errors': errors
            })
        else:
            # Regular form submission
            return super().form_invalid(form)

@method_decorator(admin_required, name='dispatch')
class RoomUpdateView(SuccessMessageMixin, UpdateView):
    model = Room
    form_class = RoomForm # <-- USE OUR CUSTOM FORM
    template_name = 'management/room_form.html'
    success_url = reverse_lazy('management:room_list')
    success_message = "Room '%(room_number)s' was updated successfully."
    
    def form_valid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request
            room = form.save()
            return JsonResponse({
                'success': True,
                'message': f"Room '{room.room_number}' was updated successfully.",
                'room_id': room.pk
            })
        else:
            # Regular form submission
            messages.success(self.request, f"Room '{form.instance.room_number}' was updated successfully.")
            return super().form_valid(form)
    
    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
            return JsonResponse({
                'success': False,
                'errors': errors
            })
        else:
            # Regular form submission
            return super().form_invalid(form)

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


# ==================== STAFF MANAGEMENT VIEWS ====================

@method_decorator(admin_required, name='dispatch')
class DoctorListView(ListView):
    model = DoctorProfile
    template_name = 'management/doctor_list.html'
    context_object_name = 'doctors'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = DoctorProfile.objects.select_related('user', 'department').all()
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(specialization__icontains=search_query) |
                Q(license_number__icontains=search_query)
            )
        
        # Department filter
        department_id = self.request.GET.get('department', '')
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        # Specialization filter
        specialization = self.request.GET.get('specialization', '')
        if specialization:
            queryset = queryset.filter(specialization__icontains=specialization)
        
        return queryset.order_by('user__first_name', 'user__last_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_doctors'] = DoctorProfile.objects.count()
        context['departments'] = Department.objects.filter(is_active=True).order_by('name')
        context['specializations'] = DoctorProfile.objects.values_list('specialization', flat=True).distinct().order_by('specialization')
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_department'] = self.request.GET.get('department', '')
        context['selected_specialization'] = self.request.GET.get('specialization', '')
        return context


@method_decorator(admin_required, name='dispatch')
class ReceptionistListView(ListView):
    model = ReceptionistProfile
    template_name = 'management/receptionist_list.html'
    context_object_name = 'receptionists'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = ReceptionistProfile.objects.select_related('user', 'department').all()
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__username__icontains=search_query)
            )
        
        # Department filter
        department_id = self.request.GET.get('department', '')
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        # Shift filter
        shift = self.request.GET.get('shift', '')
        if shift:
            queryset = queryset.filter(shift=shift)
        
        return queryset.order_by('user__first_name', 'user__last_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_receptionists'] = ReceptionistProfile.objects.count()
        context['departments'] = Department.objects.filter(is_active=True).order_by('name')
        context['shifts'] = ReceptionistProfile.SHIFT_CHOICES
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_department'] = self.request.GET.get('department', '')
        context['selected_shift'] = self.request.GET.get('shift', '')
        return context