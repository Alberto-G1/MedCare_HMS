from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import doctor_required, patient_required
from patients.models import PatientProfile
from doctors.models import DoctorProfile
from .models import Prescription
from patients.models import MedicalRecord
from .forms import PrescriptionForm, MedicationFormSet
from notifications.utils import create_notification
from django.urls import reverse
from django.http import HttpResponse, QueryDict
from django.db import models
import io


@login_required
@doctor_required
def create_prescription_view(request, patient_id):
    patient_profile = get_object_or_404(PatientProfile, pk=patient_id)
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    linked_record = None
    legacy_prescription_text = None

    # Optional linkage if coming from medical record creation
    medical_record_id = request.GET.get('medical_record')
    if medical_record_id:
        try:
            linked_record = MedicalRecord.objects.select_related('patient__user', 'doctor__user').get(id=medical_record_id, patient=patient_profile, doctor=doctor_profile)
            legacy_prescription_text = linked_record.prescription or ''
        except MedicalRecord.DoesNotExist:
            linked_record = None  # silently ignore invalid linkage

    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        med_formset = MedicationFormSet(request.POST)
        if form.is_valid() and med_formset.is_valid():
            prescription = form.save(commit=False)
            prescription.patient = patient_profile
            prescription.doctor = doctor_profile
            if linked_record:
                prescription.medical_record = linked_record
                # If doctor left notes blank but legacy text exists, port it
                if not prescription.notes and legacy_prescription_text:
                    prescription.notes = legacy_prescription_text
            prescription.save()
            med_formset.instance = prescription
            med_formset.save()
            create_notification(
                recipient=patient_profile.user,
                message=f"A new prescription (#{prescription.pk}) has been issued to you.",
                link=reverse('prescriptions:patient_prescription_detail', args=[prescription.pk])
            )
            messages.success(request, 'Prescription created successfully.')
            return redirect('prescriptions:doctor_prescription_detail', pk=prescription.pk)
    else:
        # Pre-fill notes with legacy text if any, to encourage structured migration
        initial = {}
        if legacy_prescription_text:
            initial['notes'] = legacy_prescription_text
        form = PrescriptionForm(initial=initial)
        med_formset = MedicationFormSet()

    return render(request, 'prescriptions/prescription_form.html', {
        'form': form,
        'formset': med_formset,
        'patient': patient_profile,
        'linked_record': linked_record,
    })


@login_required
@doctor_required
def prescription_detail_doctor_view(request, pk):
    prescription = get_object_or_404(Prescription.objects.select_related('patient__user', 'doctor__user'), pk=pk)
    return render(request, 'prescriptions/prescription_detail_doctor.html', {'prescription': prescription})


@login_required
@patient_required
def patient_prescription_list_view(request):
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    prescriptions = patient_profile.prescriptions.select_related('doctor__user')
    status_filter = request.GET.get('status')
    if status_filter in ['ACTIVE', 'COMPLETED', 'CANCELLED']:
        prescriptions = prescriptions.filter(status=status_filter)
    return render(request, 'prescriptions/patient_prescription_list.html', {
        'prescriptions': prescriptions,
        'status_filter': status_filter
    })


@login_required
@patient_required
def patient_prescription_detail_view(request, pk):
    patient_profile = get_object_or_404(PatientProfile, user=request.user)
    prescription = get_object_or_404(Prescription.objects.select_related('doctor__user'), pk=pk, patient=patient_profile)
    return render(request, 'prescriptions/patient_prescription_detail.html', {'prescription': prescription})


@login_required
def prescription_download_view(request, pk):
    """Generate a downloadable PDF for the prescription instead of relying on browser print."""
    prescription = get_object_or_404(Prescription.objects.select_related('patient__user', 'doctor__user'), pk=pk)
    if not (prescription.patient.user == request.user or (prescription.doctor and prescription.doctor.user == request.user)):
        messages.error(request, 'You are not authorized to download this prescription.')
        return redirect('prescriptions:patient_prescriptions')

    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.utils import ImageReader
    except ImportError:
        # Fallback: serve a plain text file if reportlab isn't installed yet.
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="prescription_{prescription.id}.txt"'
        lines = [
            f"Prescription #{prescription.id}",
            f"Patient: {prescription.patient.user.get_full_name()}",
            f"Doctor: {prescription.doctor.user.get_full_name() if prescription.doctor else 'N/A'}",
            f"Date: {prescription.created_at.strftime('%Y-%m-%d %H:%M')}",
            "",
            "Medications:",
        ]
        for m in prescription.medications.all():
            lines.append(f" - {m.medication_name} | {m.dosage} | {m.frequency} | {m.duration_days} days | {m.instructions or ''}")
        if prescription.notes:
            lines.append("\nNotes:\n" + prescription.notes)
        response.write("\n".join(lines))
        return response

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x_margin = 50
    y = height - 60

    def draw_line(text, offset=18, bold=False):
        nonlocal y
        if y < 60:
            p.showPage()
            y = height - 60
        if bold:
            p.setFont('Helvetica-Bold', 11)
        else:
            p.setFont('Helvetica', 10)
        p.drawString(x_margin, y, text)
        y -= offset

    p.setTitle(f"Prescription #{prescription.id}")
    # Header with optional logo
    logo_path = None
    try:
        from django.conf import settings
        from pathlib import Path
        potential = Path(settings.BASE_DIR) / 'templates' / 'static' / 'images' / 'logo.png'
        if potential.exists():
            logo_path = str(potential)
    except Exception:
        pass
    if logo_path:
        try:
            p.drawImage(ImageReader(logo_path), x_margin, y-20, width=60, height=60, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    p.setFont('Helvetica-Bold', 16)
    p.drawString(x_margin + (80 if logo_path else 0), y, 'MedCare Hospital')
    p.setFont('Helvetica', 9)
    p.drawString(x_margin + (80 if logo_path else 0), y-15, 'Confidential Medical Prescription')
    y -= 50
    p.setFont('Helvetica-Bold', 14)
    p.drawString(x_margin, y, f"Prescription #{prescription.id}")
    y -= 28

    draw_line(f"Patient: {prescription.patient.user.get_full_name()}", bold=True)
    draw_line(f"Doctor: {prescription.doctor.user.get_full_name() if prescription.doctor else 'N/A'}")
    draw_line(f"Issued: {prescription.created_at.strftime('%Y-%m-%d %H:%M')}")
    draw_line(f"Status: {prescription.get_status_display()}")
    y -= 10
    draw_line("Medications:", bold=True)
    for med in prescription.medications.all():
        med_line = f"• {med.medication_name} | {med.dosage} | {med.frequency} | {med.duration_days} day(s)"
        draw_line(med_line, offset=14)
        if med.instructions:
            draw_line(f"   Instructions: {med.instructions}", offset=14)

    if prescription.notes:
        y -= 10
        draw_line("Notes:", bold=True)
        for paragraph in prescription.notes.split('\n'):
            draw_line(paragraph, offset=14)

    y -= 30
    # Signature block
    p.setFont('Helvetica', 10)
    draw_line('Doctor Signature: ________________________________', offset=18)
    draw_line(f'Date: {prescription.created_at.strftime("%Y-%m-%d")}', offset=18)
    y -= 10
    p.setFont('Helvetica-Oblique', 8)
    draw_line("Generated by MedCare HMS", offset=12)
    # Finalize and return single prescription PDF
    p.showPage()
    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="prescription_{prescription.id}.pdf"'
    return response
@login_required
def prescription_batch_download_view(request):
    """Download multiple prescriptions as a single merged PDF.

    Accepts either ?ids=1,2,3 or POST with ids list.
    Only includes prescriptions the user is authorized to view.
    """
    ids_param = request.GET.get('ids') or (request.POST.get('ids') if request.method == 'POST' else '')
    id_list = []
    if ids_param:
        for part in ids_param.split(','):
            part = part.strip()
            if part.isdigit():
                id_list.append(int(part))
    qs = Prescription.objects.filter(id__in=id_list).select_related('patient__user', 'doctor__user')
    if not request.user.is_superuser:
        # Limit to prescriptions where the user is either the patient or the doctor
        qs = qs.filter(models.Q(patient__user=request.user) | models.Q(doctor__user=request.user))
    if not qs.exists():
        messages.error(request, 'No prescriptions available for batch download.')
        return redirect('prescriptions:patient_prescriptions')
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.utils import ImageReader
    except ImportError:
        response = HttpResponse('ReportLab not installed', status=500)
        return response
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    logo_path = None
    try:
        from django.conf import settings
        from pathlib import Path
        potential = Path(settings.BASE_DIR) / 'templates' / 'static' / 'images' / 'logo.png'
        if potential.exists():
            logo_path = str(potential)
    except Exception:
        pass
    for prescription in qs.order_by('id'):
        y = height - 60
        if logo_path:
            try:
                p.drawImage(ImageReader(logo_path), 50, y-20, width=60, height=60, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass
        p.setFont('Helvetica-Bold', 14)
        p.drawString(120 if logo_path else 50, y, 'MedCare Hospital - Prescription Pack')
        y -= 35
        p.setFont('Helvetica-Bold', 12)
        p.drawString(50, y, f"Prescription #{prescription.id}")
        y -= 20
        p.setFont('Helvetica', 9)
        p.drawString(50, y, f"Patient: {prescription.patient.user.get_full_name()}")
        y -= 14
        p.drawString(50, y, f"Doctor: {prescription.doctor.user.get_full_name() if prescription.doctor else 'N/A'} | Issued: {prescription.created_at.strftime('%Y-%m-%d %H:%M')}")
        y -= 18
        p.setFont('Helvetica-Bold', 10)
        p.drawString(50, y, 'Medications:')
        y -= 16
        p.setFont('Helvetica', 9)
        for med in prescription.medications.all():
            line = f"• {med.medication_name} | {med.dosage} | {med.frequency} | {med.duration_days} day(s)"
            p.drawString(55, y, line)
            y -= 14
            if med.instructions:
                p.drawString(60, y, f"Instr: {med.instructions}")
                y -= 14
            if y < 120:
                p.showPage()
                y = height - 60
        if prescription.notes:
            p.setFont('Helvetica-Bold', 10)
            p.drawString(50, y, 'Notes:')
            y -= 16
            p.setFont('Helvetica', 9)
            for para in prescription.notes.split('\n'):
                p.drawString(55, y, para[:110])
                y -= 14
                if y < 120:
                    p.showPage()
                    y = height - 60
        y -= 10
        p.setFont('Helvetica', 8)
        p.drawString(50, y, 'Doctor Signature: ______________________   Date: __________')
        p.showPage()
    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="prescriptions_batch.pdf"'
    return response
