# flyncarry/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('users.urls')),
    path('', include('itineraries.urls')),
    path('', include('bookings.urls')),
    path('', include('payments.urls')),
    path('', include('messaging.urls')),
    path('', include('admin_dashboard.urls')),
    path('', include('user_notifications.urls')),  # Updated app name
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)