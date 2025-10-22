from django.urls import path
from chat import views

app_name = 'chat'
urlpatterns = [
    path('', views.thread_list_view, name='thread_list'),
    path('thread/<int:thread_id>/', views.thread_list_view, name='thread_detail'),
    path('start/<int:user_id>/', views.start_chat_view, name='start_chat'),
    path('upload/', views.upload_file_view, name='upload_file'),
]