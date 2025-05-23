# admin_dashboard/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Avg, F, Q
from django.utils import timezone
from datetime import timedelta

from users.models import CustomUser
from bookings.models import Booking
from itineraries.models import Itinerary
from payments.models import Payment, Transaction
from .models import SystemSettings, Dispute
from .forms import SystemSettingsForm, DisputeForm, DisputeResponseForm, UserFilterForm


def is_admin(user):
    """Check if the user is an admin"""
    return user.is_authenticated and user.user_type == 'admin'


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Main admin dashboard view"""
    # Get summary statistics
    total_users = CustomUser.objects.count()
    total_travelers = CustomUser.objects.filter(user_type='traveler').count()
    total_senders = CustomUser.objects.filter(user_type='sender').count()

    total_itineraries = Itinerary.objects.count()
    active_itineraries = Itinerary.objects.filter(status='active').count()

    total_bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status='pending').count()
    completed_bookings = Booking.objects.filter(status='delivered').count()

    total_payments = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0

    # Get recent activities
    recent_users = CustomUser.objects.order_by('-date_joined')[:5]
    recent_bookings = Booking.objects.order_by('-created_at')[:5]
    recent_disputes = Dispute.objects.order_by('-created_at')[:5]

    # Get current system settings
    settings = SystemSettings.get_settings()

    return render(request, 'admin_dashboard/dashboard.html', {
        'total_users': total_users,
        'total_travelers': total_travelers,
        'total_senders': total_senders,
        'total_itineraries': total_itineraries,
        'active_itineraries': active_itineraries,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'completed_bookings': completed_bookings,
        'total_payments': total_payments,
        'recent_users': recent_users,
        'recent_bookings': recent_bookings,
        'recent_disputes': recent_disputes,
        'settings': settings,
    })


@login_required
@user_passes_test(is_admin)
def user_management(request):
    """User management view"""
    form = UserFilterForm(request.GET)

    users = CustomUser.objects.all().order_by('-date_joined')

    # Apply filters if provided
    if form.is_valid():
        user_type = form.cleaned_data.get('user_type')
        is_verified = form.cleaned_data.get('is_verified')
        date_joined_from = form.cleaned_data.get('date_joined_from')
        date_joined_to = form.cleaned_data.get('date_joined_to')

        if user_type:
            users = users.filter(user_type=user_type)

        if is_verified:
            users = users.filter(is_verified=is_verified == 'True')

        if date_joined_from:
            users = users.filter(date_joined__gte=date_joined_from)

        if date_joined_to:
            users = users.filter(date_joined__lte=date_joined_to)

    return render(request, 'admin_dashboard/user_management.html', {
        'users': users,
        'form': form,
    })


@login_required
@user_passes_test(is_admin)
def user_detail(request, user_id):
    """View details of a specific user"""
    user = get_object_or_404(CustomUser, id=user_id)

    # Get user statistics
    if user.user_type == 'traveler':
        itineraries = Itinerary.objects.filter(traveler=user)
        bookings = Booking.objects.filter(itinerary__in=itineraries)
    else:
        itineraries = []
        bookings = Booking.objects.filter(sender=user)

    payments = Payment.objects.filter(booking__in=bookings)

    return render(request, 'admin_dashboard/user_detail.html', {
        'user_detail': user,
        'itineraries': itineraries,
        'bookings': bookings,
        'payments': payments,
    })


@login_required
@user_passes_test(is_admin)
def toggle_user_verification(request, user_id):
    """Toggle a user's verification status"""
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_verified = not user.is_verified
    user.save()

    status = 'verified' if user.is_verified else 'unverified'
    messages.success(request, f"User {user.username} is now {status}.")

    return redirect('admin_user_detail', user_id=user.id)


@login_required
@user_passes_test(is_admin)
def system_settings(request):
    """Manage system settings"""
    settings = SystemSettings.get_settings()

    if request.method == 'POST':
        form = SystemSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, "System settings updated successfully.")
            return redirect('admin_system_settings')
    else:
        form = SystemSettingsForm(instance=settings)

    return render(request, 'admin_dashboard/system_settings.html', {
        'form': form,
        'settings': settings,
    })


@login_required
@user_passes_test(is_admin)
def dispute_list(request):
    """List all disputes"""
    disputes = Dispute.objects.all().order_by('-created_at')

    return render(request, 'admin_dashboard/dispute_list.html', {
        'disputes': disputes,
    })


@login_required
@user_passes_test(is_admin)
def dispute_detail(request, dispute_id):
    """View and manage a specific dispute"""
    dispute = get_object_or_404(Dispute, id=dispute_id)

    if request.method == 'POST':
        form = DisputeResponseForm(request.POST, instance=dispute)
        if form.is_valid():
            dispute = form.save(commit=False)
            dispute.assigned_to = request.user
            dispute.save()
            messages.success(request, "Dispute updated successfully.")
            return redirect('admin_dispute_detail', dispute_id=dispute.id)
    else:
        form = DisputeResponseForm(instance=dispute)

    return render(request, 'admin_dashboard/dispute_detail.html', {
        'dispute': dispute,
        'form': form,
    })


@login_required
@user_passes_test(is_admin)
def reports(request):
    """Generate various reports for admin"""
    # Date ranges
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    # User statistics
    user_stats = {
        'total': CustomUser.objects.count(),
        'travelers': CustomUser.objects.filter(user_type='traveler').count(),
        'senders': CustomUser.objects.filter(user_type='sender').count(),
        'new_30_days': CustomUser.objects.filter(date_joined__gte=thirty_days_ago).count(),
    }

    # Booking statistics
    booking_stats = {
        'total': Booking.objects.count(),
        'pending': Booking.objects.filter(status='pending').count(),
        'confirmed': Booking.objects.filter(status='confirmed').count(),
        'in_transit': Booking.objects.filter(status='in_transit').count(),
        'delivered': Booking.objects.filter(status='delivered').count(),
        'cancelled': Booking.objects.filter(status='cancelled').count(),
        'new_30_days': Booking.objects.filter(created_at__gte=thirty_days_ago).count(),
    }

    # Payment statistics
    payment_stats = {
        'total_amount': Payment.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0,
        'average_amount': Payment.objects.filter(status='completed').aggregate(avg=Avg('amount'))['avg'] or 0,
        'total_30_days':
            Payment.objects.filter(status='completed', created_at__gte=thirty_days_ago).aggregate(total=Sum('amount'))[
                'total'] or 0,
    }

    # Popular routes
    popular_routes = Itinerary.objects.values('origin', 'destination').annotate(
        count=Count('bookings')
    ).order_by('-count')[:5]

    return render(request, 'admin_dashboard/reports.html', {
        'user_stats': user_stats,
        'booking_stats': booking_stats,
        'payment_stats': payment_stats,
        'popular_routes': popular_routes,
    })