# user_notifications/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<uuid:notification_id>/mark-read/', views.mark_as_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_as_read, name='mark_all_notifications_read'),
    path('notifications/unread-count/', views.unread_count, name='notification_unread_count'),
    path('notifications/<uuid:notification_id>/view/', views.view_notification, name='view_notification'),
]