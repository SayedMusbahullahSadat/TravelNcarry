# bookings/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('bookings/', views.BookingListView.as_view(), name='booking_list'),
    path('bookings/<uuid:pk>/', views.BookingDetailView.as_view(), name='booking_detail'),
    path('bookings/create/<uuid:itinerary_id>/', views.create_booking, name='create_booking'),
    path('bookings/<uuid:pk>/update-status/', views.update_booking_status, name='update_booking_status'),
    path('bookings/<uuid:pk>/cancel/', views.cancel_booking, name='cancel_booking'),

    path('package-requests/', views.PackageRequestListView.as_view(), name='package_request_list'),
    path('package-requests/<uuid:pk>/', views.PackageRequestDetailView.as_view(), name='package_request_detail'),
    path('package-requests/create/', views.create_package_request, name='create_package_request'),
    path('package-requests/<uuid:pk>/cancel/', views.cancel_package_request, name='cancel_package_request'),
    path('package-requests/<uuid:pk>/accept/', views.accept_package_request, name='accept_package_request'),
]