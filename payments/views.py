# payments/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from decimal import Decimal
import json

from bookings.models import Booking
from .models import Payment, Transaction
from .forms import PaymentMethodForm
from .payment_service import PaymentService


@login_required
def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Check if user is the sender
    if request.user != booking.sender:
        messages.error(request, "You are not authorized to make this payment.")
        return redirect('booking_detail', pk=booking_id)

    # Check if booking status is valid
    if booking.status != 'pending':
        messages.error(request, f"This booking is already in {booking.get_status_display()} status.")
        return redirect('booking_detail', pk=booking_id)

    # Get or create payment
    payment, created = Payment.objects.get_or_create(
        booking=booking,
        defaults={'amount': booking.price, 'status': 'pending'}
    )

    if request.method == 'POST':
        # Collect card information
        card_info = {
            'card_number': request.POST.get('card_number'),
            'expiry_month': request.POST.get('expiry_month'),
            'expiry_year': request.POST.get('expiry_year'),
            'cvc': request.POST.get('cvc'),
            'name_on_card': request.POST.get('name_on_card')
        }

        # Store payment ID in session for use after 3D redirect
        request.session['payment_id'] = str(payment.id)

        # Initiate 3D Secure payment
        success, response = PaymentService.initiate_3d_payment(payment, card_info, request)

        if success:
            # Return the HTML content that will redirect to 3D Secure page
            return HttpResponse(response)
        else:
            messages.error(request, f"Payment failed: {response}")

    return render(request, 'payments/payment_page.html', {
        'booking': booking,
        'payment': payment
    })


@login_required
def iyzico_3d_callback(request):
    """
    Callback endpoint for Iyzico 3D Secure authentication.
    """
    if request.method == 'POST':
        # Get the payment ID from session
        payment_id = request.session.get('payment_id')

        if not payment_id:
            messages.error(request, "Payment session expired or invalid.")
            return redirect('booking_list')

        # Process the 3D authentication result
        success, message = PaymentService.complete_3d_payment(
            payment_id,
            {
                'conversationId': request.POST.get('conversationId'),
                'paymentId': request.POST.get('paymentId'),
                'conversationData': request.POST.get('conversationData'),
            }
        )

        payment = Payment.objects.get(id=payment_id)

        if success:
            messages.success(request, "Payment processed successfully!")
            return redirect('payment_success', payment_id=payment.id)
        else:
            messages.error(request, f"Payment failed: {message}")
            return redirect('payment_page', booking_id=payment.booking.id)

    messages.error(request, "Invalid payment response.")
    return redirect('booking_list')


@login_required
def process_payment(request, booking_id):
    """
    Process a payment with Iyzico.
    """
    booking = get_object_or_404(Booking, id=booking_id)

    # Check if user is the sender
    if request.user != booking.sender:
        messages.error(request, "You are not authorized to make this payment.")
        return redirect('booking_detail', pk=booking_id)

    # Check if booking status is valid
    if booking.status != 'pending':
        messages.error(request, f"This booking is already in {booking.get_status_display()} status.")
        return redirect('booking_detail', pk=booking_id)

    # Get or create payment
    payment, created = Payment.objects.get_or_create(
        booking=booking,
        defaults={'amount': booking.price, 'status': 'pending'}
    )

    if request.method == 'POST':
        # Collect card information
        card_info = {
            'card_number': request.POST.get('card_number'),
            'expiry_month': request.POST.get('expiry_month'),
            'expiry_year': request.POST.get('expiry_year'),
            'cvc': request.POST.get('cvc'),
            'name_on_card': request.POST.get('name_on_card')
        }

        # Process payment
        success, message = PaymentService.process_payment(payment, card_info)

        if success:
            messages.success(request, "Payment processed successfully!")
            return redirect('payment_success', payment_id=payment.id)
        else:
            messages.error(request, f"Payment failed: {message}")
            return redirect('payment_page', booking_id=booking_id)

    return redirect('payment_page', booking_id=booking_id)


@login_required
def payment_success(request, payment_id):
    """
    Display payment success page.
    """
    payment = get_object_or_404(Payment, id=payment_id)

    # Check if user is the sender
    if request.user != payment.booking.sender:
        messages.error(request, "You are not authorized to view this payment.")
        return redirect('booking_list')

    return render(request, 'payments/payment_success.html', {
        'payment': payment,
        'booking': payment.booking,
    })


@login_required
def release_payment(request, booking_id):
    """
    Release payment to the traveler when delivery is confirmed.
    """
    booking = get_object_or_404(Booking, id=booking_id)

    # Check if the user is the sender
    if request.user != booking.sender:
        messages.error(request, "You are not authorized to release this payment.")
        return redirect('booking_detail', pk=booking_id)

    # Check if the booking is delivered
    if booking.status != 'delivered':
        messages.error(request, "Payment can only be released for delivered packages.")
        return redirect('booking_detail', pk=booking_id)

    # Get the payment
    payment = get_object_or_404(Payment, booking=booking)

    if payment.status != 'completed':
        messages.error(request, "Payment must be completed before it can be released.")
        return redirect('booking_detail', pk=booking_id)

    # Release the payment
    success, message = PaymentService.release_to_traveler(payment)

    if success:
        messages.success(request, "Payment has been released to the traveler.")
    else:
        messages.error(request, f"Failed to release payment: {message}")

    return redirect('booking_detail', pk=booking_id)


@login_required
def cancel_and_refund(request, booking_id):
    """
    Cancel a booking and refund the payment.
    """
    booking = get_object_or_404(Booking, id=booking_id)

    # Check if the user is the sender
    if request.user != booking.sender:
        messages.error(request, "You are not authorized to cancel this booking.")
        return redirect('booking_detail', pk=booking_id)

    # Check if the booking can be cancelled
    if booking.status not in ['confirmed', 'pending']:
        messages.error(request, f"Cannot cancel a booking that is {booking.get_status_display().lower()}.")
        return redirect('booking_detail', pk=booking_id)

    # Get the payment
    try:
        payment = Payment.objects.get(booking=booking)
    except Payment.DoesNotExist:
        messages.error(request, "No payment found for this booking.")
        return redirect('booking_detail', pk=booking_id)

    if payment.status != 'completed':
        messages.error(request, "Only completed payments can be refunded.")
        return redirect('booking_detail', pk=booking_id)

    # Refund the payment
    success, message = PaymentService.refund_payment(payment)

    if success:
        messages.success(request, "Booking cancelled and payment refunded successfully.")
    else:
        messages.error(request, f"Failed to refund payment: {message}")

    return redirect('booking_detail', pk=booking_id)


@login_required
def payment_history(request):
    """
    Display payment history for the user.
    """
    user = request.user

    if user.user_type == 'sender':
        payments = Payment.objects.filter(booking__sender=user).order_by('-created_at')
    elif user.user_type == 'traveler':
        payments = Payment.objects.filter(booking__itinerary__traveler=user).order_by('-created_at')
    else:
        payments = Payment.objects.none()

    return render(request, 'payments/payment_history.html', {
        'payments': payments,
    })