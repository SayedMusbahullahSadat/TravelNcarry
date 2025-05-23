# admin_dashboard/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/users/', views.user_management, name='admin_user_management'),
    path('admin-dashboard/users/<int:user_id>/', views.user_detail, name='admin_user_detail'),
    path('admin-dashboard/users/<int:user_id>/toggle-verification/', views.toggle_user_verification, name='admin_toggle_user_verification'),
    path('admin-dashboard/settings/', views.system_settings, name='admin_system_settings'),
    path('admin-dashboard/disputes/', views.dispute_list, name='admin_dispute_list'),
    path('admin-dashboard/disputes/<int:dispute_id>/', views.dispute_detail, name='admin_dispute_detail'),
    path('admin-dashboard/reports/', views.reports, name='admin_reports'),
]