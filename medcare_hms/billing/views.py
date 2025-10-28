# billing/views.py (FINAL VERSION)

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Sum, Q, Count, DecimalField
from decimal import Decimal, InvalidOperation
from patients.models import Appointment, PatientProfile
from .models import Bill, BillItem
from .forms import BillForm, BillItemForm, UpdatePaymentForm
from accounts.decorators import receptionist_required
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import date
from django.urls import reverse
from notifications.utils import create_notification 
from .filters import BillFilter
from django.http import HttpResponse
import io
from audit.utils import audit_log

staff_decorators = [login_required, receptionist_required]

@method_decorator(staff_decorators, name='dispatch')
class BillListView(ListView):
    model = Bill
    template_name = 'billing/bill_list.html'
    context_object_name = 'bills'
    
    def get_queryset(self):
        """
        This method now handles the filtering directly.
        """
        # Start with the base queryset
        queryset = Bill.objects.select_related('patient__user', 'patient__user__patientprofile').order_by('-bill_date')
        
        # Apply the django-filter FilterSet
        self.filterset = BillFilter(self.request.GET, queryset=queryset)
        
        # Return the filtered queryset
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        """
        This method adds the filter form and statistics to the context.
        """
        context = super().get_context_data(**kwargs)
        today = date.today()
        
        # Add the filter form to the context
        context['filter'] = self.filterset
        context['bills'] = self.filterset.qs
        
        # # Aggregate statistics for the dashboard cards
        paid_stats = Bill.objects.filter(status='Paid').aggregate(count=Count('id'), total=Coalesce(Sum('total_amount'), 0, output_field=DecimalField()))
        unpaid_stats = Bill.objects.filter(status='Unpaid').aggregate(count=Count('id'), total=Coalesce(Sum('total_amount'), 0, output_field=DecimalField()))
        partially_paid_stats = Bill.objects.filter(status='Partially Paid').aggregate(count=Count('id'), total=Coalesce(Sum('amount_paid'), 0, output_field=DecimalField())) # Sum amount_paid for this card
        overdue_stats = Bill.objects.filter(status='Unpaid', due_date__lt=today).aggregate(count=Count('id'), total=Coalesce(Sum('total_amount'), 0, output_field=DecimalField()))
        
        context['paid_bills_count'] = paid_stats['count']
        context['paid_bills_total'] = paid_stats['total']
        context['unpaid_bills_count'] = unpaid_stats['count']
        context['unpaid_bills_total'] = unpaid_stats['total']
        context['partially_paid_bills_count'] = partially_paid_stats['count']
        context['partially_paid_bills_total'] = partially_paid_stats['total']
        context['overdue_bills_count'] = overdue_stats['count']
        context['overdue_bills_total'] = overdue_stats['total']
        
        return context
    
        # context = super().get_context_data(**kwargs)
        # today = date.today()
        
        # # Apply the filter to the queryset
        # bill_filter = BillFilter(self.request.GET, queryset=self.get_queryset())
        # context['filter'] = bill_filter
        # context['bills'] = bill_filter.qs
        # # Aggregate statistics for the dashboard cards
        # paid_stats = Bill.objects.filter(status='Paid').aggregate(count=Count('id'), total=Coalesce(Sum('total_amount'), 0, output_field=DecimalField()))
        # unpaid_stats = Bill.objects.filter(status='Unpaid').aggregate(count=Count('id'), total=Coalesce(Sum('total_amount'), 0, output_field=DecimalField()))
        # partially_paid_stats = Bill.objects.filter(status='Partially Paid').aggregate(count=Count('id'), total=Coalesce(Sum('amount_paid'), 0, output_field=DecimalField())) # Sum amount_paid for this card
        # overdue_stats = Bill.objects.filter(status='Unpaid', due_date__lt=today).aggregate(count=Count('id'), total=Coalesce(Sum('total_amount'), 0, output_field=DecimalField()))
        
        # context['paid_bills_count'] = paid_stats['count']
        # context['paid_bills_total'] = paid_stats['total']
        # context['unpaid_bills_count'] = unpaid_stats['count']
        # context['unpaid_bills_total'] = unpaid_stats['total']
        # context['partially_paid_bills_count'] = partially_paid_stats['count']
        # context['partially_paid_bills_total'] = partially_paid_stats['total']
        # context['overdue_bills_count'] = overdue_stats['count']
        # context['overdue_bills_total'] = overdue_stats['total']
        
        # # THE INCORRECT LINE HAS BEEN REMOVED FROM HERE
        
        # return context

@method_decorator(staff_decorators, name='dispatch')
class BillDetailView(DetailView):
    model = Bill
    template_name = 'billing/bill_detail.html'
    context_object_name = 'bill'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['item_form'] = BillItemForm() # Pass the form for adding new items
        context['item_form'] = BillItemForm()
        context['payment_form'] = UpdatePaymentForm(instance=self.object)
        return context

@login_required
@receptionist_required
def create_bill_view(request):
    if request.method == 'POST':
        form = BillForm(request.POST)
        if form.is_valid():
            bill = form.save()
            audit_log(actor=request.user, action='CREATE', target=bill, summary=f"Created bill for {bill.patient.user.username}")

            # --- NOTIFICATION LOGIC ---
            patient_user = bill.patient.user
            message = f"A new miscellaneous bill (ID: #{bill.pk}) has been generated for you."
            create_notification(recipient=patient_user, message=message, link=reverse('patients:my_bills_list'))
            # --- END NOTIFICATION LOGIC ---

            messages.success(request, f"New bill created for {bill.patient.user.username}. You can now add items.")
            return redirect('billing:bill_detail', pk=bill.pk)
    else:
        form = BillForm()
    
    context = {'form': form}
    return render(request, 'billing/create_bill.html', context)

@login_required
@receptionist_required
def add_bill_item_view(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id)
    if request.method == 'POST':
        form = BillItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.bill = bill
            item.save()
            audit_log(actor=request.user, action='CREATE', target=item, summary=f"Added item {item.description} to bill {bill.pk}")
            
            # Recalculate the bill's total amount
            total = bill.items.aggregate(total=Sum('amount'))['total'] or 0.00
            bill.total_amount = total
            bill.save()

            messages.success(request, f"Item '{item.description}' added to Bill #{bill.pk}.")
    return redirect('billing:bill_detail', pk=bill.pk)

@login_required
@receptionist_required
def update_payment_status_view(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id)
    if request.method == 'POST':
        form = UpdatePaymentForm(request.POST, instance=bill) # Not used, but good practice
        
        new_status = request.POST.get('status')
        new_payment_str = request.POST.get('new_payment_amount', '0')
        
        try:
            # --- THIS IS THE FIX: Convert the input to a Decimal ---
            new_payment = Decimal(new_payment_str if new_payment_str else '0.00')
        except InvalidOperation:
            messages.error(request, "Invalid payment amount entered.")
            return redirect('billing:bill_detail', pk=bill.pk)

        if new_status == 'Paid':
            bill.amount_paid = bill.total_amount
            bill.status = 'Paid'
            messages.success(request, f"Bill #{bill.id} has been marked as Fully Paid.")
        
        elif new_status == 'Partially Paid':
            if new_payment <= 0:
                messages.error(request, "Please enter a payment amount greater than zero for a partial payment.")
                return redirect('billing:bill_detail', pk=bill.pk)
            
            bill.amount_paid += new_payment
            
            if bill.amount_paid >= bill.total_amount:
                bill.amount_paid = bill.total_amount
                bill.status = 'Paid'
                messages.success(request, f"Final payment of {new_payment:,.2f} received. Bill #{bill.id} is now Fully Paid.")
            else:
                bill.status = 'Partially Paid'
                messages.info(request, f"Partial payment of UGX {new_payment:,.0f} recorded for Bill #{bill.id}.")

        elif new_status == 'Unpaid':
            bill.amount_paid = Decimal('0.00') # Use a Decimal for consistency
            bill.status = 'Unpaid'
            messages.warning(request, f"Bill #{bill.id} status has been reset to Unpaid.")
        
        # Only update payment_method if it was provided in the form
        payment_method = request.POST.get('payment_method')
        if payment_method:
            bill.payment_method = payment_method
        
        bill.save()
    audit_log(actor=request.user, action='UPDATE', target=bill, summary=f"Payment status updated to {bill.status}", details={'fields': ['status','amount_paid']})

    return redirect('billing:bill_detail', pk=bill.pk)

@method_decorator(staff_decorators, name='dispatch')
class BillReceiptView(DetailView):
    model = Bill
    template_name = 'billing/bill_receipt.html'
    context_object_name = 'bill'


@login_required
@receptionist_required
def bill_pdf_view(request, pk):
    """Generate a downloadable PDF invoice/receipt for a single bill."""
    bill = get_object_or_404(Bill.objects.select_related('patient__user'), pk=pk)
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.utils import ImageReader
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import Table, TableStyle
    except ImportError:
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="bill_{bill.pk}.txt"'
        lines = [
            f"Bill #{bill.pk}",
            f"Patient: {bill.patient.user.get_full_name()}",
            f"Status: {bill.status}",
            f"Total: {bill.total_amount}",
            f"Paid: {bill.amount_paid}",
            f"Due: {bill.amount_due}",
            "Items:",
        ]
        for item in bill.items.all():
            lines.append(f" - {item.description} x{item.quantity} @ {item.unit_price} = {item.amount}")
        response.write("\n".join(lines))
        return response
    
    # Modern color scheme matching the web design
    PRIMARY_TEAL = colors.HexColor('#0E7490')
    SKY_BLUE = colors.HexColor('#0284C7')
    LIGHT_BLUE = colors.HexColor('#E0F2FE')
    GREEN = colors.HexColor('#22C55E')
    LIGHT_GREEN = colors.HexColor('#D1FAE5')
    RED = colors.HexColor('#EF4444')
    LIGHT_RED = colors.HexColor('#FEE2E2')
    ORANGE = colors.HexColor('#F59E0B')
    LIGHT_ORANGE = colors.HexColor('#FEF3C7')
    GRAY_700 = colors.HexColor('#374151')
    GRAY_600 = colors.HexColor('#4B5563')
    GRAY_200 = colors.HexColor('#E5E7EB')
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin_x = 40
    y = height - 40

    # Load assets (logo + patient profile picture)
    logo_path = None
    patient_photo_path = None
    try:
        from django.conf import settings
        from pathlib import Path
        static_logo = Path(settings.BASE_DIR) / 'static' / 'images' / 'logo.png'
        if static_logo.exists():
            logo_path = str(static_logo)
        # Patient picture
        if bill.patient.profile_picture and bill.patient.profile_picture.name:
            media_candidate = Path(settings.BASE_DIR) / bill.patient.profile_picture.name
            if media_candidate.exists():
                patient_photo_path = str(media_candidate)
            else:
                # Try default image
                default_img = Path(settings.BASE_DIR) / 'static' / 'images' / 'default.jpeg'
                if default_img.exists():
                    patient_photo_path = str(default_img)
    except Exception:
        pass

    # ==================== HEADER SECTION (Gradient Effect) ====================
    # Gradient header band - Teal to Sky Blue
    header_height = 80
    # Draw gradient by layering rectangles with varying opacity
    for i in range(10):
        alpha = 1.0 - (i * 0.1)
        r = 0.055 + (i * 0.006)  # Teal to Sky Blue
        g = 0.455 + (i * 0.065)
        b = 0.565
        p.setFillColorRGB(r, g, b, alpha=0.8)
        rect_y = y - header_height + (i * 8)
        p.rect(0, rect_y, width, 8, fill=1, stroke=0)
    
    # Header content
    p.setFillColor(colors.white)
    if logo_path:
        try:
            p.drawImage(ImageReader(logo_path), margin_x, y - 60, width=50, height=50, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    # Company name
    p.setFont('Helvetica-Bold', 22)
    p.drawString(margin_x + (60 if logo_path else 0), y - 25, 'MedCare HMS')
    p.setFont('Helvetica', 11)
    p.drawString(margin_x + (60 if logo_path else 0), y - 42, 'Hospital Management System')

    # Invoice badge
    badge_x = width - margin_x - 130
    p.setFillColor(colors.white)
    p.setStrokeColor(colors.white)
    p.setLineWidth(2)
    p.roundRect(badge_x, y - 60, 130, 50, 8, stroke=1, fill=0)
    p.setFont('Helvetica', 9)
    p.drawCentredString(badge_x + 65, y - 30, 'Invoice Number')
    p.setFont('Helvetica-Bold', 16)
    p.drawCentredString(badge_x + 65, y - 50, f"MED-{bill.pk:05d}")
    
    y -= header_height + 20

    # ==================== BILLING INFO SECTION ====================
    # Light blue background
    info_box_height = 120
    p.setFillColor(LIGHT_BLUE)
    p.rect(margin_x - 10, y - info_box_height, width - 2*margin_x + 20, info_box_height, fill=1, stroke=0)
    
    # Patient section with photo
    p.setFillColor(PRIMARY_TEAL)
    p.setFont('Helvetica-Bold', 10)
    p.drawString(margin_x, y - 15, 'BILLED TO')
    
    # Patient photo
    photo_size = 60
    if patient_photo_path:
        try:
            p.drawImage(ImageReader(patient_photo_path), margin_x, y - 90, width=photo_size, height=photo_size, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    
    # Patient details
    p.setFillColor(GRAY_700)
    p.setFont('Helvetica-Bold', 14)
    p.drawString(margin_x + photo_size + 10, y - 35, bill.patient.user.get_full_name())
    p.setFont('Helvetica', 10)
    p.setFillColor(GRAY_600)
    p.drawString(margin_x + photo_size + 10, y - 50, bill.patient.user.email or '')
    
    # Invoice details (right side)
    detail_x = width - margin_x - 200
    p.setFillColor(PRIMARY_TEAL)
    p.setFont('Helvetica-Bold', 10)
    p.drawString(detail_x, y - 15, 'INVOICE DETAILS')
    
    p.setFillColor(GRAY_700)
    p.setFont('Helvetica', 10)
    p.drawString(detail_x, y - 35, f"Date Issued:")
    p.drawString(detail_x + 80, y - 35, bill.bill_date.strftime('%B %d, %Y'))
    
    p.drawString(detail_x, y - 52, f"Due Date:")
    p.drawString(detail_x + 80, y - 52, bill.due_date.strftime('%B %d, %Y') if bill.due_date else 'N/A')
    
    p.drawString(detail_x, y - 69, f"Payment Method:")
    p.drawString(detail_x + 80, y - 69, bill.payment_method or 'N/A')
    
    y -= info_box_height + 30

    # ==================== ITEMS SECTION ====================
    p.setFillColor(GRAY_700)
    p.setFont('Helvetica-Bold', 14)
    p.drawString(margin_x, y, 'Bill Items')
    y -= 25

    # Items table header
    p.setFillColor(PRIMARY_TEAL)
    p.rect(margin_x, y - 20, width - 2*margin_x, 20, fill=1, stroke=0)
    
    p.setFillColor(colors.white)
    p.setFont('Helvetica-Bold', 10)
    p.drawString(margin_x + 5, y - 13, '#')
    p.drawString(margin_x + 30, y - 13, 'Description')
    p.drawRightString(margin_x + 300, y - 13, 'Qty')
    p.drawRightString(margin_x + 400, y - 13, 'Unit Price')
    p.drawRightString(width - margin_x - 5, y - 13, 'Amount')
    y -= 25

    # Items rows
    p.setFont('Helvetica', 10)
    for idx, item in enumerate(bill.items.all(), 1):
        if y < 150:
            p.showPage()
            y = height - 60
        
        # Alternating row colors
        if idx % 2 == 0:
            p.setFillColor(colors.HexColor('#F9FAFB'))
            p.rect(margin_x, y - 18, width - 2*margin_x, 18, fill=1, stroke=0)
        
        p.setFillColor(PRIMARY_TEAL)
        p.drawString(margin_x + 5, y - 12, str(idx))
        p.setFillColor(GRAY_700)
        p.drawString(margin_x + 30, y - 12, item.description[:50])
        p.drawRightString(margin_x + 300, y - 12, str(item.quantity))
        p.drawRightString(margin_x + 400, y - 12, f"UGX {item.unit_price:,.0f}")
        p.setFont('Helvetica-Bold', 10)
        p.drawRightString(width - margin_x - 5, y - 12, f"UGX {item.amount:,.0f}")
        p.setFont('Helvetica', 10)
        y -= 20

    y -= 20

    # ==================== TOTALS SECTION ====================
    totals_width = 250
    totals_x = width - margin_x - totals_width
    
    # Light gray background
    p.setFillColor(colors.HexColor('#F9FAFB'))
    totals_height = 90 if bill.status == 'Partially Paid' else 60
    p.roundRect(totals_x, y - totals_height, totals_width, totals_height, 10, fill=1, stroke=0)
    
    # Subtotal
    p.setFillColor(GRAY_700)
    p.setFont('Helvetica', 11)
    p.drawString(totals_x + 10, y - 20, 'Subtotal:')
    p.drawRightString(totals_x + totals_width - 10, y - 20, f"UGX {bill.total_amount:,.0f}")
    
    y -= 25
    
    # If partially paid, show paid and due
    if bill.status == 'Partially Paid':
        p.setFillColor(GREEN)
        p.drawString(totals_x + 10, y - 10, 'Amount Paid:')
        p.drawRightString(totals_x + totals_width - 10, y - 10, f"UGX {bill.amount_paid:,.0f}")
        y -= 20
        
        # Amount due with red background
        p.setFillColor(LIGHT_RED)
        p.roundRect(totals_x + 5, y - 22, totals_width - 10, 20, 5, fill=1, stroke=0)
        p.setFillColor(RED)
        p.setFont('Helvetica-Bold', 11)
        p.drawString(totals_x + 10, y - 15, 'Amount Due:')
        p.drawRightString(totals_x + totals_width - 10, y - 15, f"UGX {bill.amount_due:,.0f}")
        y -= 25
    
    # Grand total
    p.setStrokeColor(PRIMARY_TEAL)
    p.setLineWidth(2)
    p.line(totals_x + 10, y, totals_x + totals_width - 10, y)
    p.setFillColor(GRAY_700)
    p.setFont('Helvetica-Bold', 13)
    p.drawString(totals_x + 10, y - 20, 'Total Amount:')
    p.drawRightString(totals_x + totals_width - 10, y - 20, f"UGX {bill.total_amount:,.0f}")
    
    y -= 40

    # ==================== STATUS AND FOOTER ====================
    # Status badge
    badge_width = 150
    badge_height = 40
    status_x = margin_x
    
    if bill.status == 'Paid':
        badge_color = LIGHT_GREEN
        text_color = colors.HexColor('#065F46')
        icon = '✓'
    elif bill.status == 'Unpaid':
        badge_color = LIGHT_RED
        text_color = colors.HexColor('#991B1B')
        icon = '✗'
    else:
        badge_color = LIGHT_ORANGE
        text_color = colors.HexColor('#92400E')
        icon = '!'
    
    p.setFillColor(badge_color)
    p.setStrokeColor(text_color)
    p.setLineWidth(3)
    p.roundRect(status_x, y - badge_height, badge_width, badge_height, 10, fill=1, stroke=1)
    
    p.setFillColor(text_color)
    p.setFont('Helvetica-Bold', 18)
    p.drawCentredString(status_x + badge_width/2, y - 28, f"{icon} {bill.status.upper()}")
    
    # Thank you message
    p.setFillColor(GRAY_700)
    p.setFont('Helvetica-Bold', 13)
    p.drawRightString(width - margin_x, y - 15, 'Thank You!')
    p.setFont('Helvetica', 10)
    p.setFillColor(GRAY_600)
    p.drawRightString(width - margin_x, y - 30, 'MedCare Hospital Management System')
    
    # Footer
    p.setFont('Helvetica', 8)
    p.setFillColor(GRAY_600)
    p.drawCentredString(width/2, 30, f"Generated on {bill.bill_date.strftime('%B %d, %Y')}")

    p.showPage()
    p.save()
    pdf = buffer.getvalue()
    buffer.close()

    # Build friendly filename
    first_name = bill.patient.user.first_name or bill.patient.user.username
    safe_first = first_name.replace(' ', '_')
    filename = f"{safe_first}'s_Bill_MED{bill.pk:05d}.pdf"

    resp = HttpResponse(pdf, content_type='application/pdf')
    resp['Content-Disposition'] = f"attachment; filename=\"{filename}\""
    return resp

@login_required
@receptionist_required
def bill_batch_pdf_view(request):
    """Generate a merged PDF for multiple bills (?ids=1,2,3)."""
    ids_param = request.GET.get('ids','')
    id_list = [int(p.strip()) for p in ids_param.split(',') if p.strip().isdigit()]
    qs = Bill.objects.filter(pk__in=id_list).select_related('patient__user')
    if not qs.exists():
        messages.error(request,'No bills selected for batch export.')
        return redirect('billing:bill_list')
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.utils import ImageReader
    except ImportError:
        return HttpResponse('ReportLab not installed', status=500)
    buffer = io.BytesIO(); p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Preload logo if available
    logo_path = None
    try:
        from django.conf import settings
        from pathlib import Path
        static_logo = Path(settings.BASE_DIR) / 'static' / 'images' / 'logo.png'
        if static_logo.exists():
            logo_path = str(static_logo)
    except Exception:
        pass

    for bill in qs.order_by('pk'):
        margin_x = 40
        y = height - 50

        # Header band
        header_height = 55
        p.setFillColorRGB(0.95, 0.95, 0.98)
        p.rect(0, y - header_height + 15, width, header_height, fill=1, stroke=0)
        p.setFillColorRGB(0,0,0)
        if logo_path:
            try:
                p.drawImage(ImageReader(logo_path), margin_x, y - 38, width=50, height=50, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass
        p.setFont('Helvetica-Bold', 18)
        p.drawString(margin_x + (60 if logo_path else 0), y - 5, 'MedCare Hospital')
        p.setFont('Helvetica', 9)
        p.drawString(margin_x + (60 if logo_path else 0), y - 20, 'Batch Billing Statement')
        y -= 65

        # Patient / Bill meta (without explicit Bill # label to keep professional tone)
        p.setFont('Helvetica-Bold', 12)
        full_name = bill.patient.user.get_full_name() or bill.patient.user.username
        p.drawString(margin_x, y, full_name)
        y -= 18
        p.setFont('Helvetica', 10)
        p.drawString(margin_x, y, f"Bill Date: {bill.bill_date.strftime('%Y-%m-%d')}")
        y -= 14
        if bill.due_date:
            p.drawString(margin_x, y, f"Due Date: {bill.due_date.strftime('%Y-%m-%d')}")
            y -= 14
        p.drawString(margin_x, y, f"Status: {bill.status}")
        y -= 14
        p.drawString(margin_x, y, f"Payment Method: {bill.payment_method or 'N/A'}")
        y -= 20

        # Items table header
        p.setStrokeColorRGB(0.75,0.75,0.85); p.setLineWidth(0.6)
        p.line(margin_x, y, width - margin_x, y)
        y -= 16
        p.setFont('Helvetica-Bold', 10)
        p.drawString(margin_x, y, 'Description')
        p.drawString(margin_x + 250, y, 'Qty')
        p.drawString(margin_x + 300, y, 'Unit Price')
        p.drawString(margin_x + 400, y, 'Amount')
        y -= 14
        p.setLineWidth(0.4)
        p.line(margin_x, y, width - margin_x, y)
        y -= 10

        p.setFont('Helvetica', 10)
        for item in bill.items.all():
            if y < 90:
                p.showPage(); y = height - 60
                # Re-draw table header on new page
                p.setFont('Helvetica-Bold', 10)
                p.drawString(margin_x, y, 'Description')
                p.drawString(margin_x + 250, y, 'Qty')
                p.drawString(margin_x + 300, y, 'Unit Price')
                p.drawString(margin_x + 400, y, 'Amount')
                y -= 14
                p.line(margin_x, y, width - margin_x, y)
                y -= 10
                p.setFont('Helvetica', 10)
            p.drawString(margin_x, y, item.description[:45])
            p.drawRightString(margin_x + 280, y, str(item.quantity))
            p.drawRightString(margin_x + 380, y, f"{item.unit_price}")
            p.drawRightString(width - margin_x, y, f"{item.amount}")
            y -= 16

        # Summary line
        y -= 8
        p.setFont('Helvetica-Bold', 10)
        p.drawString(margin_x, y, f"Total: {bill.total_amount}   Paid: {bill.amount_paid}   Due: {bill.amount_due}")
        y -= 30
        p.setFont('Helvetica-Oblique',8)
        p.setFillColorRGB(0.4,0.4,0.4)
        p.drawString(margin_x, y, 'Generated by MedCare HMS')
        p.showPage()

    p.save(); pdf = buffer.getvalue(); buffer.close()

    # Friendly filename logic for batch: If one bill, mimic single; if multiple, use first name + count.
    if qs.count() == 1:
        first = qs.first().patient.user.first_name or qs.first().patient.user.username
        safe_first = first.replace(' ', '_')
        filename = f"{safe_first}'s Bill.pdf" if not safe_first.endswith("'s") else f"{safe_first} Bill.pdf"
    else:
        first = qs.first().patient.user.first_name or qs.first().patient.user.username
        safe_first = first.replace(' ', '_')
        filename = f"{safe_first}_and_{qs.count()-1}_others_Bills.pdf"

    resp = HttpResponse(pdf, content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp


@login_required
@receptionist_required
def select_appointment_for_billing(request):
    """
    Step 1: Display a list of completed appointments that don't have a bill yet.
    """
    # Get IDs of appointments that already have a bill
    billed_appointment_ids = Bill.objects.exclude(appointment__isnull=True).values_list('appointment_id', flat=True)
    
    # Find appointments that are 'Completed' and are not yet billed
    unbilled_appointments = Appointment.objects.filter(status='Completed').exclude(id__in=billed_appointment_ids)
    
    context = {
        'appointments': unbilled_appointments
    }
    return render(request, 'billing/select_appointment.html', context)

@login_required
@receptionist_required
def create_bill_from_appointment(request, appointment_id):
    """
    Step 2: Automatically create a bill linked to the selected appointment and patient.
    """
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    
    # Check if a bill already exists for this appointment to prevent duplicates
    if Bill.objects.filter(appointment=appointment).exists():
        messages.error(request, "A bill already exists for this appointment.")
        return redirect('billing:select_appointment')

    # Automatically create the bill
    bill = Bill.objects.create(
        patient=appointment.patient,
        appointment=appointment
    )
    
    # Optional: Pre-populate with a consultation fee
    BillItem.objects.create(
        bill=bill,
        description=f"Consultation with {appointment.doctor}",
        quantity=1,
        unit_price=50000 # Example price in UGX
    )
    
    # Recalculate total
    total = bill.items.aggregate(total=Sum('amount'))['total'] or 0.00
    bill.total_amount = total
    bill.save()

    # --- NOTIFICATION LOGIC ---
    patient_user = bill.patient.user
    message = f"A new bill (ID: #{bill.pk}) has been generated for you."
    create_notification(recipient=patient_user, message=message, link=reverse('patients:my_bills_list'))
    # --- END NOTIFICATION LOGIC ---

    messages.success(request, "Bill created successfully. You can now add more items.")
    return redirect('billing:bill_detail', pk=bill.pk)

@login_required
@receptionist_required
def edit_bill_item_view(request, pk):
    item = get_object_or_404(BillItem, pk=pk)
    bill = item.bill
    
    # Prevent editing of the initial consultation fee
    if "Consultation with" in item.description:
        messages.error(request, "The primary consultation fee cannot be edited.")
        return redirect('billing:bill_detail', pk=bill.pk)

    if request.method == 'POST':
        form = BillItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            # Recalculate total
            total = bill.items.aggregate(total=Sum('amount'))['total'] or 0.00
            bill.total_amount = total
            bill.save()
            messages.success(request, "Bill item updated successfully.")
            return redirect('billing:bill_detail', pk=bill.pk)
    else:
        form = BillItemForm(instance=item)
    
    return render(request, 'billing/edit_bill_item.html', {'form': form, 'item': item})

@login_required
@receptionist_required
def delete_bill_item_view(request, pk):
    item = get_object_or_404(BillItem, pk=pk)
    bill = item.bill

    # Prevent deleting of the initial consultation fee
    if "Consultation with" in item.description:
        messages.error(request, "The primary consultation fee cannot be deleted.")
        return redirect('billing:bill_detail', pk=bill.pk)

    if request.method == 'POST':
        audit_log(actor=request.user, action='DELETE', target=item, summary=f"Deleted item {item.description} from bill {bill.pk}")
        item.delete()
        # Recalculate total
        total = bill.items.aggregate(total=Sum('amount'))['total'] or 0.00
        bill.total_amount = total
        bill.save()
        messages.success(request, "Bill item deleted successfully.")
        return redirect('billing:bill_detail', pk=bill.pk)

    return render(request, 'billing/delete_bill_item_confirm.html', {'item': item})

@login_required
@receptionist_required
def delete_bill_view(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if request.method == 'POST':
        patient_name = bill.patient.user.get_full_name
        audit_log(actor=request.user, action='DELETE', target=bill, summary=f"Deleted bill {bill.pk}")
        bill.delete()
        messages.success(request, f"Bill #{pk} for {patient_name} has been successfully deleted.")
        return redirect('billing:bill_list')
    
    return render(request, 'billing/delete_bill_confirm.html', {'bill': bill})