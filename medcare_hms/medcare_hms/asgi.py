import os
from django.core.asgi import get_asgi_application

# Initialize Django's settings FIRST.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medcare_hms.settings')
django_asgi_app = get_asgi_application()

# Import Channels and routing AFTER Django is initialized.
from channels.auth import AuthMiddlewareStack # <-- Use this one
from channels.routing import ProtocolTypeRouter, URLRouter
from medcare_hms import routing

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_asgi_app,
    
    # WebSocket chat handler
    "websocket": AuthMiddlewareStack( # <-- This is the key
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})