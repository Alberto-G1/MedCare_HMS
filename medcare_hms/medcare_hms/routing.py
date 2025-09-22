from django.urls import re_path
from chat import consumers 

websocket_urlpatterns = [
    # This pattern now correctly matches the URL your JavaScript is trying to connect to.
    re_path(r'ws/chat/(?P<thread_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
]