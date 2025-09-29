from django.contrib import admin
from .models import Prescription, PrescribedMedication


class PrescribedMedicationInline(admin.TabularInline):
    model = PrescribedMedication
    extra = 0


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'status', 'created_at')
    list_filter = ('status', 'doctor')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'doctor__user__first_name', 'doctor__user__last_name')
    inlines = [PrescribedMedicationInline]
