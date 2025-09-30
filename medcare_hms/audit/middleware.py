import uuid
from django.utils.deprecation import MiddlewareMixin

class CorrelationIdMiddleware(MiddlewareMixin):
    """Attach a correlation_id to each request for audit grouping."""
    def process_request(self, request):
        request.correlation_id = request.headers.get('X-Correlation-ID') or uuid.uuid4().hex
