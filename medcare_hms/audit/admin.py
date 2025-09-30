from django.contrib import admin
from .models import SystemLog

@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('created_at','action','actor','target_model','target_id','correlation_id','summary')
    list_filter = ('action','target_model','created_at')
    search_fields = ('summary','details','target_model','target_id','actor__username','correlation_id')
    readonly_fields = ('created_at',)

    change_list_template = 'admin/audit/systemlog/change_list.html'

    def changelist_view(self, request, extra_context=None):
        # Provide quick date ranges
        from django.utils import timezone
        now = timezone.now()
        extra_context = extra_context or {}
        extra_context['quick_ranges'] = [
            ('24h', (now - timezone.timedelta(hours=24)).isoformat()),
            ('7d', (now - timezone.timedelta(days=7)).isoformat()),
            ('30d', (now - timezone.timedelta(days=30)).isoformat()),
        ]
        return super().changelist_view(request, extra_context=extra_context)
