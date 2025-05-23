# itineraries/api_views.py
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Itinerary
from .serializers import ItinerarySerializer
from django.shortcuts import get_object_or_404


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.traveler == request.user


class ItineraryViewSet(viewsets.ModelViewSet):
    queryset = Itinerary.objects.all()
    serializer_class = ItinerarySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['origin', 'destination', 'departure_date', 'status']
    search_fields = ['origin', 'destination']
    ordering_fields = ['departure_date', 'created_at']

    def perform_create(self, serializer):
        serializer.save(traveler=self.request.user)

    def get_queryset(self):
        queryset = Itinerary.objects.all()
        if self.action == 'my_itineraries':
            return queryset.filter(traveler=self.request.user)
        return queryset

    @action(detail=False, methods=['get'])
    def my_itineraries(self, request):
        itineraries = self.get_queryset()
        page = self.paginate_queryset(itineraries)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(itineraries, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        itinerary = self.get_object()
        itinerary.status = 'cancelled'
        itinerary.save()
        serializer = self.get_serializer(itinerary)
        return Response(serializer.data)