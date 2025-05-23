# itineraries/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'itineraries', api_views.ItineraryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]