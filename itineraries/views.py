# itineraries/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q, Count, F, Avg
from bookings.models import PackageRequest

from .models import Itinerary, SavedSearch
from .forms import ItineraryForm, ItinerarySearchForm


class ItineraryListView(ListView):
    model = Itinerary
    template_name = 'itineraries/itinerary_list.html'
    context_object_name = 'itineraries'
    paginate_by = 10

    def get_queryset(self):
        queryset = Itinerary.objects.filter(status='active').order_by('departure_date', 'departure_time')

        # Apply search filters
        form = ItinerarySearchForm(self.request.GET)
        if form.is_valid():
            origin = form.cleaned_data.get('origin')
            destination = form.cleaned_data.get('destination')
            departure_date_from = form.cleaned_data.get('departure_date_from')
            departure_date_to = form.cleaned_data.get('departure_date_to')
            min_capacity = form.cleaned_data.get('min_capacity')
            max_capacity = form.cleaned_data.get('max_capacity')
            min_price = form.cleaned_data.get('min_price')
            max_price = form.cleaned_data.get('max_price')
            min_rating = form.cleaned_data.get('min_rating')
            verified_only = form.cleaned_data.get('verified_only')
            sort_by = form.cleaned_data.get('sort_by')

            if origin:
                queryset = queryset.filter(origin__icontains=origin)
            if destination:
                queryset = queryset.filter(destination__icontains=destination)

            # Date range filtering
            if departure_date_from:
                queryset = queryset.filter(departure_date__gte=departure_date_from)
            if departure_date_to:
                queryset = queryset.filter(departure_date__lte=departure_date_to)

            # Rating filter
            if min_rating:
                queryset = queryset.filter(traveler__average_rating__gte=min_rating)

            # Verified travelers only
            if verified_only:
                queryset = queryset.filter(traveler__is_verified=True)

            # Sort results
            if sort_by:
                queryset = queryset.order_by(sort_by)

            # These filters require post-processing in Python
            # Filter by capacity
            if min_capacity:
                queryset = [itinerary for itinerary in queryset if
                            itinerary.available_capacity() >= float(min_capacity)]
            if max_capacity:
                queryset = [itinerary for itinerary in queryset if
                            itinerary.available_capacity() <= float(max_capacity)]

            # For price filtering, we'd need to calculate the price based on the system pricing
            # This is a simplified version - actual implementation would depend on your pricing logic
            if min_price or max_price:
                from admin_dashboard.models import SystemSettings
                settings = SystemSettings.get_settings()

                filtered_itineraries = []
                for itinerary in queryset:
                    # Calculate a sample price for a 1kg package
                    sample_price = settings.calculate_price(1.0)

                    if min_price and sample_price < float(min_price):
                        continue
                    if max_price and sample_price > float(max_price):
                        continue

                    filtered_itineraries.append(itinerary)

                queryset = filtered_itineraries

        # Calculate used capacity percentage for each itinerary
        for itinerary in queryset:
            if float(itinerary.capacity_kg) > 0:  # Avoid division by zero
                itinerary.used_capacity_percent = int(
                    (float(itinerary.capacity_kg) - float(itinerary.available_capacity())) / float(
                        itinerary.capacity_kg) * 100)
            else:
                itinerary.used_capacity_percent = 0

        return queryset

    def get_context_data(self, **kwargs):
        # Keep all existing functionality
        context = super().get_context_data(**kwargs)
        context['search_form'] = ItinerarySearchForm(self.request.GET)

        # Add information about applied filters for display (keep this code unchanged)
        applied_filters = {}
        for key, value in self.request.GET.items():
            if value and key != 'page' and key != 'sort_by':
                applied_filters[key] = value

        context['applied_filters'] = applied_filters

        # ADD NEW CODE: Get package requests that match the search criteria
        package_requests = PackageRequest.objects.filter(status='open')

        # Apply similar filters as used for itineraries
        form = ItinerarySearchForm(self.request.GET)
        if form.is_valid():
            origin = form.cleaned_data.get('origin')
            destination = form.cleaned_data.get('destination')
            departure_date_from = form.cleaned_data.get('departure_date_from')
            departure_date_to = form.cleaned_data.get('departure_date_to')

            # Apply origin/destination filters
            if origin:
                package_requests = package_requests.filter(origin__icontains=origin)
            if destination:
                package_requests = package_requests.filter(destination__icontains=destination)

            # Apply date filters (using preferred_date in PackageRequest)
            if departure_date_from:
                package_requests = package_requests.filter(preferred_date__gte=departure_date_from)
            if departure_date_to:
                package_requests = package_requests.filter(preferred_date__lte=departure_date_to)

        # Add package requests to the context
        context['package_requests'] = package_requests

        return context


class MyItinerariesListView(LoginRequiredMixin, ListView):
    model = Itinerary
    template_name = 'itineraries/my_itineraries.html'
    context_object_name = 'itineraries'

    def get_queryset(self):
        return Itinerary.objects.filter(traveler=self.request.user).order_by('-created_at')


class ItineraryDetailView(DetailView):
    model = Itinerary
    template_name = 'itineraries/itinerary_detail.html'
    context_object_name = 'itinerary'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        itinerary = self.get_object()

        # Assuming we'll later have a Booking model
        # context['bookings'] = Booking.objects.filter(itinerary=itinerary)

        return context


class ItineraryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Itinerary
    form_class = ItineraryForm
    template_name = 'itineraries/itinerary_form.html'
    success_url = reverse_lazy('my_itineraries')

    def form_valid(self, form):
        form.instance.traveler = self.request.user
        messages.success(self.request, 'Itinerary created successfully!')
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.user_type == 'traveler'

    def handle_no_permission(self):
        messages.error(self.request, 'Only travelers can create itineraries.')
        return redirect('home')


class ItineraryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Itinerary
    form_class = ItineraryForm
    template_name = 'itineraries/itinerary_form.html'

    def get_success_url(self):
        return reverse_lazy('itinerary_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Itinerary updated successfully!')
        return super().form_valid(form)

    def test_func(self):
        itinerary = self.get_object()
        return self.request.user == itinerary.traveler

    def handle_no_permission(self):
        messages.error(self.request, 'You can only edit your own itineraries.')
        return redirect('itinerary_list')


class ItineraryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Itinerary
    template_name = 'itineraries/itinerary_confirm_delete.html'
    success_url = reverse_lazy('my_itineraries')

    def test_func(self):
        itinerary = self.get_object()
        return self.request.user == itinerary.traveler

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Itinerary deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
def save_search(request):
    if request.method == 'POST':
        name = request.POST.get('search_name')
        if not name:
            messages.error(request, "Please provide a name for your saved search.")
            return redirect('itinerary_list')

        # Create a new saved search with current parameters
        saved_search = SavedSearch(
            user=request.user,
            name=name,
            origin=request.GET.get('origin', ''),
            destination=request.GET.get('destination', ''),
            notify=request.POST.get('notify', False) == 'on'
        )

        # Handle date fields
        departure_date_from = request.GET.get('departure_date_from')
        if departure_date_from:
            saved_search.departure_date_from = departure_date_from

        departure_date_to = request.GET.get('departure_date_to')
        if departure_date_to:
            saved_search.departure_date_to = departure_date_to

        # Handle numeric fields
        min_capacity = request.GET.get('min_capacity')
        if min_capacity:
            saved_search.min_capacity = min_capacity

        max_capacity = request.GET.get('max_capacity')
        if max_capacity:
            saved_search.max_capacity = max_capacity

        min_price = request.GET.get('min_price')
        if min_price:
            saved_search.min_price = min_price

        max_price = request.GET.get('max_price')
        if max_price:
            saved_search.max_price = max_price

        min_rating = request.GET.get('min_rating')
        if min_rating:
            saved_search.min_rating = min_rating

        verified_only = request.GET.get('verified_only')
        if verified_only:
            saved_search.verified_only = True

        saved_search.save()
        messages.success(request, f"Search '{name}' saved successfully.")

    return redirect('itinerary_list')


@login_required
def saved_searches(request):
    searches = SavedSearch.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'itineraries/saved_searches.html', {'searches': searches})


@login_required
def delete_saved_search(request, search_id):
    search = get_object_or_404(SavedSearch, id=search_id, user=request.user)

    if request.method == 'POST':
        search.delete()
        messages.success(request, f"Saved search '{search.name}' deleted successfully.")
        return redirect('saved_searches')

    return render(request, 'itineraries/delete_saved_search.html', {'search': search})