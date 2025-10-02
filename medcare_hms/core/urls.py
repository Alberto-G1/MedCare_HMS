from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('features/', views.features_view, name='features'),
    path('about/', views.about_view, name='about'),
    path('team/', views.team_view, name='team'),
    path('team/detail/', views.team_detail_view, name='team_detail'),
    path('contact/', views.contact_view, name='contact'),
]