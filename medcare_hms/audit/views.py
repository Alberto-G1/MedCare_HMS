from django.http import JsonResponse, Http404, HttpResponse
import re
from django.shortcuts import render
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from accounts.decorators import admin_required
from .models import SystemLog
from datetime import datetime, timedelta
from django.db.models import Q
import csv

@login_required
@admin_required
def recent_audit_events(request):
    limit = int(request.GET.get('limit', 50))
    limit = min(limit, 200)
    qs = SystemLog.objects.all().select_related('actor')[:limit]
    data = [
        {
            'ts': log.created_at.isoformat(),
            'action': log.action,
            'actor': log.actor.username if log.actor else None,
            'target_model': log.target_model,
            'target_id': log.target_id,
            'summary': log.summary,
            'correlation_id': log.correlation_id,
        }
        for log in qs
    ]
    return JsonResponse({'results': data})

@login_required
def audit_feed(request):
    """Read-only HTML feed for staff (non-admin also allowed) with filtering & optional CSV export"""
    action = request.GET.get('action')
    correlation_id = request.GET.get('correlation') or request.GET.get('cid')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    actor_search = request.GET.get('actor')
    export = request.GET.get('export')
    q = SystemLog.objects.all().select_related('actor')
    if action:
        q = q.filter(action=action)
    if correlation_id:
        q = q.filter(correlation_id__icontains=correlation_id)
    if actor_search:
        q = q.filter(Q(actor__username__icontains=actor_search) | Q(actor__first_name__icontains=actor_search) | Q(actor__last_name__icontains=actor_search))
    start_date = None
    end_date = None
    date_format = "%Y-%m-%d"
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, date_format)
            q = q.filter(created_at__gte=start_date)
        except ValueError:
            start_date_str = None  # invalid input ignored
    if end_date_str:
        try:
            # Add one day to make end date inclusive up to end of day
            end_date = datetime.strptime(end_date_str, date_format) + timedelta(days=1)
            q = q.filter(created_at__lt=end_date)
        except ValueError:
            end_date_str = None
    q = q.order_by('-created_at')
    # CSV export (before pagination)
    if export == 'csv':
        # Hard cap to prevent memory blow-up; could allow a higher cap or stream
        max_rows = 5000
        rows = q[:max_rows]
        response = HttpResponse(content_type='text/csv')
        filename_parts = ["audit"]
        if start_date_str:
            filename_parts.append(start_date_str)
        if end_date_str:
            filename_parts.append(end_date_str)
        filename = "_".join(filename_parts) + ".csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(['timestamp','action','actor','target_model','target_id','summary','correlation_id'])
        for log in rows:
            writer.writerow([
                log.created_at.isoformat(),
                log.action,
                log.actor.username if log.actor else '',
                log.target_model,
                log.target_id,
                log.summary,
                log.correlation_id,
            ])
        if q.count() > max_rows:
            writer.writerow([f"TRUNCATED to {max_rows} rows"])
        return response
    try:
        page_size = int(request.GET.get('page_size', 50))
    except ValueError:
        page_size = 25
    if page_size not in (5, 10, 15, 20, 25, 50, 100, 200):
        page_size = 25
    paginator = Paginator(q, page_size)
    page_obj = paginator.get_page(request.GET.get('page'))
    actions = SystemLog.objects.values_list('action', flat=True).distinct()
    context = {
        'page_obj': page_obj,
        'actions': actions,
        'selected_action': action,
        'selected_correlation_id': correlation_id or '',
        'page_size': page_size,
        'start_date': start_date_str or '',
        'end_date': end_date_str or '',
        'actor_search': actor_search or '',
    }
    return render(request, 'audit/audit_feed.html', context)

@login_required
def correlation_detail(request, correlation_id):
    original = correlation_id
    # If correlation_id is 32 hex chars without hyphens, format it to UUID style
    if re.fullmatch(r'[0-9a-fA-F]{32}', correlation_id):
        correlation_id = f"{correlation_id[0:8]}-{correlation_id[8:12]}-{correlation_id[12:16]}-{correlation_id[16:20]}-{correlation_id[20:32]}".lower()
    logs = (SystemLog.objects
            .filter(correlation_id__in=[original, correlation_id])
            .select_related('actor')
            .order_by('created_at'))
    if not logs.exists():
        raise Http404('No events for this correlation id')
    return render(request, 'audit/correlation_detail.html', {
        'correlation_id': correlation_id,
        'logs': logs,
    })