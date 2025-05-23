# itineraries/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('itineraries/', views.ItineraryListView.as_view(), name='itinerary_list'),
    path('itineraries/my/', views.MyItinerariesListView.as_view(), name='my_itineraries'),
    path('itineraries/<uuid:pk>/', views.ItineraryDetailView.as_view(), name='itinerary_detail'),
    path('itineraries/create/', views.ItineraryCreateView.as_view(), name='itinerary_create'),
    path('itineraries/<uuid:pk>/update/', views.ItineraryUpdateView.as_view(), name='itinerary_update'),
    path('itineraries/<uuid:pk>/delete/', views.ItineraryDeleteView.as_view(), name='itinerary_delete'),
    path('itineraries/save-search/', views.save_search, name='save_search'),
    path('itineraries/saved-searches/', views.saved_searches, name='saved_searches'),
    path('itineraries/saved-searches/<int:search_id>/delete/', views.delete_saved_search, name='delete_saved_search'),
]

