# payments/webhooks.py
import json
import hmac
import hashlib
import base64
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import Payment, Transaction


@csrf_exempt
@require_POST
def iyzico_webhook(request):
    """
    Handle webhook notifications from Iyzico
    """
    payload = request.body

    # Get the signature from headers
    iyzico_signature = request.META.get('HTTP_X_IYZWS_SIGNATURE', '')

    # Verify the signature (adjust according to Iyzico's signature verification method)
    # Example of HMAC signature verification (check Iyzico's documentation for exact details)
    expected_signature = generate_iyzico_signature(payload, settings.IYZICO_SECRET_KEY)

    if not hmac.compare_digest(iyzico_signature, expected_signature):
        return HttpResponse(status=400)

    # Parse the payload
    try:
        event_data = json.loads(payload)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    # Handle different event types
    event_type = event_data.get('eventType')

    if event_type == 'PAYMENT_COMPLETED':
        handle_iyzico_payment_completed(event_data)
    elif event_type == 'PAYMENT_FAILED':
        handle_iyzico_payment_failed(event_data)
    elif event_type == 'PAYMENT_REFUNDED':
        handle_iyzico_payment_refunded(event_data)
    # Add more event types as needed

    return HttpResponse(status=200)


def generate_iyzico_signature(payload, secret_key):
    """
    Generate a signature for Iyzico webhook verification
    """
    # This is an example - check Iyzico's documentation for the exact method
    hash_obj = hmac.new(secret_key.encode(), payload, hashlib.sha256)
    return base64.b64encode(hash_obj.digest()).decode()


def handle_iyzico_payment_completed(event_data):
    """
    Handle successful payment notification from Iyzico
    """
    payment_id = event_data.get('paymentId')
    if not payment_id:
        return

    try:
        # Find the payment by Iyzico payment ID
        payment = Payment.objects.get(iyzico_payment_id=payment_id)

        # Update payment status
        payment.status = 'completed'
        payment.save()

        # Create transaction record
        Transaction.objects.create(
            payment=payment,
            amount=payment.amount,
            transaction_type='payment',
            status='succeeded',
            transaction_id=payment_id
        )

        # Update booking status
        booking = payment.booking
        booking.status = 'confirmed'
        booking.save()

    except Payment.DoesNotExist:
        # Handle missing payment record
        pass


def handle_iyzico_payment_failed(event_data):
    """
    Handle failed payment notification from Iyzico
    """
    payment_id = event_data.get('paymentId')
    if not payment_id:
        return

    try:
        payment = Payment.objects.get(iyzico_payment_id=payment_id)
        payment.status = 'failed'
        payment.save()
    except Payment.DoesNotExist:
        pass


def handle_iyzico_payment_refunded(event_data):
    """
    Handle refund notification from Iyzico
    """
    payment_id = event_data.get('paymentId')
    if not payment_id:
        return

    try:
        payment = Payment.objects.get(iyzico_payment_id=payment_id)
        payment.status = 'refunded'
        payment.save()

        # Create transaction record for refund
        Transaction.objects.create(
            payment=payment,
            amount=payment.amount,  # Might need to get actual refund amount from event_data
            transaction_type='refund',
            status='succeeded',
            transaction_id=event_data.get('refundTransactionId', f'refund_{payment_id}')
        )

        # Update booking status
        booking = payment.booking
        booking.status = 'cancelled'
        booking.save()

    except Payment.DoesNotExist:
        pass