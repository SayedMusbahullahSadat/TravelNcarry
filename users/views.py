# users/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import CustomUser, Rating
from .forms import CustomUserChangeForm, RatingForm


class ProfileDetailView(DetailView):
    model = CustomUser
    template_name = 'users/profile_detail.html'
    context_object_name = 'profile_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['ratings'] = Rating.objects.filter(to_user=user).order_by('-created_at')
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'users/profile_update.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('profile_detail', kwargs={'pk': self.request.user.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully')
        return super().form_valid(form)


@login_required
def create_rating(request, booking_id):
    # Import the Booking model here to avoid circular imports
    from bookings.models import Booking

    # Get the booking with the provided UUID
    booking = get_object_or_404(Booking, id=booking_id)

    # Check if user is authorized to rate
    if request.user != booking.sender and request.user != booking.itinerary.traveler:
        messages.error(request, 'You are not authorized to rate this transaction')
        return redirect('booking_detail', pk=booking_id)

    # Determine who to rate
    to_user = booking.itinerary.traveler if request.user == booking.sender else booking.sender

    # Check if already rated - Use booking_id instead of booking
    if Rating.objects.filter(from_user=request.user, booking_id=booking.id).exists():
        messages.error(request, 'You have already rated this transaction')
        return redirect('booking_detail', pk=booking_id)

    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.from_user = request.user
            rating.to_user = to_user
            # Use booking_id instead of booking
            rating.booking_id = booking.id
            rating.save()
            messages.success(request, 'Rating submitted successfully')
            return redirect('booking_detail', pk=booking_id)
    else:
        form = RatingForm()

    return render(request, 'users/create_rating.html', {
        'form': form,
        'booking': booking,
        'to_user': to_user,
    })