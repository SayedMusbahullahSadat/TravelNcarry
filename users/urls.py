# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('profile/<int:pk>/', views.ProfileDetailView.as_view(), name='profile_detail'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_update'),
    path('rating/create/<uuid:booking_id>/', views.create_rating, name='create_rating'),
]