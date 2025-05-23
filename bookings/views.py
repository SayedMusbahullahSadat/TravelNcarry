# bookings/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from decimal import Decimal
from django.db import transaction
import datetime
from user_notifications.services import NotificationService


from .models import Booking, PackageRequest
from .forms import BookingForm, PackageRequestForm, BookingStatusUpdateForm
from itineraries.models import Itinerary

# Set this based on admin configuration, per kg price
PRICE_PER_KG = Decimal('10.00')


class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'sender':
            return Booking.objects.filter(sender=user).order_by('-created_at')
        elif user.user_type == 'traveler':
            return Booking.objects.filter(itinerary__traveler=user).order_by('-created_at')
        else:
            return Booking.objects.none()


class BookingDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Booking
    template_name = 'bookings/booking_detail.html'
    context_object_name = 'booking'

    def test_func(self):
        booking = self.get_object()
        user = self.request.user
        return user == booking.sender or user == booking.itinerary.traveler

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = self.get_object()
        if self.request.user == booking.itinerary.traveler and booking.status == 'pending':
            context['status_form'] = BookingStatusUpdateForm(instance=booking)
        return context


@login_required
def create_booking(request, itinerary_id):
    itinerary = get_object_or_404(Itinerary, pk=itinerary_id)

    # Check if user is a sender
    if request.user.user_type != 'sender':
        messages.error(request, 'Only senders can create bookings.')
        return redirect('itinerary_detail', pk=itinerary_id)

    # Check if itinerary is active
    if itinerary.status != 'active':
        messages.error(request, 'This itinerary is no longer available for booking.')
        return redirect('itinerary_detail', pk=itinerary_id)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)

            # Check available capacity
            if float(booking.package_weight) > itinerary.available_capacity():
                messages.error(request,
                               f'The package weight exceeds the available capacity of {itinerary.available_capacity()} kg.')
                return render(request, 'bookings/booking_form.html', {'form': form, 'itinerary': itinerary})

            booking.sender = request.user
            booking.itinerary = itinerary

            # Calculate price
            booking.price = booking.package_weight * PRICE_PER_KG

            booking.save()
            messages.success(request, 'Booking request submitted successfully!')
            return redirect('booking_detail', pk=booking.pk)
    else:
        form = BookingForm()

    return render(request, 'bookings/booking_form.html', {
        'form': form,
        'itinerary': itinerary
    })


@login_required
def update_booking_status(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    # Check if user is the traveler for this booking
    if request.user != booking.itinerary.traveler:
        messages.error(request, 'You are not authorized to update this booking.')
        return redirect('booking_detail', pk=pk)

    if request.method == 'POST':
        form = BookingStatusUpdateForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, 'Booking status updated successfully!')
            return redirect('booking_detail', pk=pk)

    return redirect('booking_detail', pk=pk)


@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    # Check if user is the sender or traveler for this booking
    if request.user != booking.sender and request.user != booking.itinerary.traveler:
        messages.error(request, 'You are not authorized to cancel this booking.')
        return redirect('booking_detail', pk=pk)

    # Check if booking can be cancelled
    if booking.status in ['delivered', 'cancelled']:
        messages.error(request, f'Cannot cancel a booking that is already {booking.get_status_display().lower()}.')
        return redirect('booking_detail', pk=pk)

    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, 'Booking cancelled successfully!')
        return redirect('booking_list')

    return render(request, 'bookings/booking_confirm_cancel.html', {'booking': booking})


class PackageRequestListView(LoginRequiredMixin, ListView):
    model = PackageRequest
    template_name = 'bookings/package_request_list.html'
    context_object_name = 'package_requests'

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'sender':
            return PackageRequest.objects.filter(sender=user).order_by('-created_at')
        elif user.user_type == 'traveler':
            return PackageRequest.objects.filter(status='open').order_by('-created_at')
        else:
            return PackageRequest.objects.none()


class PackageRequestDetailView(LoginRequiredMixin, DetailView):
    model = PackageRequest
    template_name = 'bookings/package_request_detail.html'
    context_object_name = 'package_request'


@login_required
def create_package_request(request):
    if request.user.user_type != 'sender':
        messages.error(request, 'Only senders can create package requests.')
        return redirect('home')

    if request.method == 'POST':
        form = PackageRequestForm(request.POST)
        if form.is_valid():
            package_request = form.save(commit=False)
            package_request.sender = request.user
            package_request.save()
            messages.success(request, 'Package request created successfully!')
            return redirect('package_request_detail', pk=package_request.pk)
    else:
        form = PackageRequestForm()

    return render(request, 'bookings/package_request_form.html', {'form': form})


@login_required
def cancel_package_request(request, pk):
    package_request = get_object_or_404(PackageRequest, pk=pk)

    if request.user != package_request.sender:
        messages.error(request, 'You are not authorized to cancel this package request.')
        return redirect('package_request_detail', pk=pk)

    if package_request.status != 'open':
        messages.error(request,
                       f'Cannot cancel a package request that is already {package_request.get_status_display().lower()}.')
        return redirect('package_request_detail', pk=pk)

    if request.method == 'POST':
        package_request.status = 'cancelled'
        package_request.save()
        messages.success(request, 'Package request cancelled successfully!')
        return redirect('package_request_list')

    return render(request, 'bookings/package_request_confirm_cancel.html', {'package_request': package_request})


@login_required
def accept_package_request(request, pk):
    package_request = get_object_or_404(PackageRequest, pk=pk)

    if request.user.user_type != 'traveler':
        messages.error(request, 'Only travelers can accept package requests.')
        return redirect('package_request_detail', pk=pk)

    if package_request.status != 'open':
        messages.error(request, 'This package request is no longer open for acceptance.')
        return redirect('package_request_detail', pk=pk)

    # If the form was submitted with time and capacity details
    if request.method == 'POST':
        try:
            # Get form data
            departure_time_str = request.POST.get('departure_time', '12:00')
            arrival_time_str = request.POST.get('arrival_time', '12:00')
            arrival_date_str = request.POST.get('arrival_date')
            capacity_kg = request.POST.get('capacity_kg', 0)

            # Parse times
            try:
                departure_time = datetime.datetime.strptime(departure_time_str, '%H:%M').time()
            except ValueError:
                departure_time = datetime.time(12, 0)  # Default to noon

            try:
                arrival_time = datetime.datetime.strptime(arrival_time_str, '%H:%M').time()
            except ValueError:
                arrival_time = datetime.time(12, 0)  # Default to noon

            # Parse arrival date
            try:
                if arrival_date_str:
                    arrival_date = datetime.datetime.strptime(arrival_date_str, '%Y-%m-%d').date()
                else:
                    arrival_date = package_request.preferred_date + datetime.timedelta(days=1)  # Default to next day
            except ValueError:
                arrival_date = package_request.preferred_date + datetime.timedelta(days=1)  # Default to next day

            # Convert capacity to float with a minimum of the package weight
            try:
                capacity_kg = float(capacity_kg)
                if capacity_kg < float(package_request.package_weight):
                    capacity_kg = float(package_request.package_weight) * 1.5  # 50% buffer
            except (ValueError, TypeError):
                capacity_kg = float(package_request.package_weight) * 2  # Default to double if parsing fails

            # Start a database transaction to ensure all operations complete or none do
            with transaction.atomic():
                # Create a new itinerary for the traveler
                itinerary = Itinerary(
                    traveler=request.user,
                    origin=package_request.origin,
                    destination=package_request.destination,
                    departure_date=package_request.preferred_date,
                    departure_time=departure_time,
                    arrival_date=arrival_date,
                    arrival_time=arrival_time,
                    capacity_kg=capacity_kg,
                    package_restrictions=package_request.special_instructions,
                    status='active'
                )
                itinerary.save()

                # Create a booking from this request
                booking = Booking(
                    sender=package_request.sender,
                    itinerary=itinerary,
                    package_description=package_request.package_description,
                    package_weight=package_request.package_weight,
                    package_dimensions=package_request.package_dimensions,
                    special_instructions=package_request.special_instructions,
                    price=package_request.price_offer,
                    status='confirmed'  # Directly confirmed since it's an accepted request
                )
                booking.save()

                # Update the package request status
                package_request.status = 'accepted'
                package_request.save()

                # Create notifications for both parties
                # Notify the sender
                NotificationService.create_notification(
                    user=package_request.sender,
                    notification_type='booking',
                    title='Package Request Accepted',
                    message=f'Your package request from {package_request.origin} to {package_request.destination} has been accepted by {request.user.username}.',
                    link=f'/bookings/{booking.id}/'
                )

                # Notify the traveler (confirmation)
                NotificationService.create_notification(
                    user=request.user,
                    notification_type='booking',
                    title='Package Request Accepted',
                    message=f'You have accepted a package request from {package_request.origin} to {package_request.destination}.',
                    link=f'/bookings/{booking.id}/'
                )

                messages.success(request, 'Package request accepted successfully! An itinerary and booking have been created.')
                return redirect('booking_detail', pk=booking.pk)

        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('package_request_detail', pk=pk)

    # If not POST, show the form to gather additional details
    return render(request, 'bookings/accept_package_request.html', {
        'package_request': package_request
    })