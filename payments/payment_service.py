# payments/payment_service.py
from decimal import Decimal
from django.db import transaction
from .models import Payment, Transaction
from .iyzico_service import iyzico_service


class PaymentService:
    """
    Service for handling payments and transactions.
    """

    @staticmethod
    def create_payment(booking):
        """
        Create a new payment for a booking.
        """
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.price,
            status='pending'
        )
        return payment

    @staticmethod
    def process_payment(payment, card_info):
        """
        Process a payment through the payment gateway (Iyzico).
        """
        with transaction.atomic():
            try:
                # Create payment in Iyzico
                iyzico_response = iyzico_service.create_payment(
                    payment.booking.sender,
                    payment.booking,
                    card_info
                )

                # Save the payment ID
                payment.iyzico_payment_id = iyzico_response.get('paymentId')
                payment.save()

                # Check payment status
                if iyzico_response.get('status') == 'success':
                    payment.status = 'completed'
                    payment.save()

                    # Create transaction record
                    Transaction.objects.create(
                        payment=payment,
                        amount=payment.amount,
                        transaction_type='payment',
                        status='succeeded',
                        transaction_id=iyzico_response.get('paymentId')
                    )

                    # Update booking status
                    booking = payment.booking
                    booking.status = 'confirmed'
                    booking.save()

                    return True, "Payment processed successfully."
                else:
                    payment.status = 'failed'
                    payment.save()

                    error_msg = iyzico_response.get('errorMessage', "Payment processing failed.")
                    return False, error_msg

            except Exception as e:
                payment.status = 'failed'
                payment.save()

                return False, str(e)

    @staticmethod
    def initiate_3d_payment(payment, card_info, request):
        """
        Initiate a 3D Secure payment through Iyzico.
        Returns HTML content to redirect to 3D Secure page.
        """
        with transaction.atomic():
            try:
                # Create 3D Secure payment in Iyzico
                iyzico_response = iyzico_service.create_3d_payment(
                    payment.booking.sender,
                    payment.booking,
                    card_info,
                    request
                )

                # Check the response
                if iyzico_response.get('status') == 'success':
                    # Save the conversation ID for later use
                    payment.iyzico_payment_id = iyzico_response.get('conversationId')
                    payment.save()

                    # Return the HTML content that will redirect to 3D Secure page
                    return True, iyzico_response.get('threeDSHtmlContent')
                else:
                    payment.status = 'failed'
                    payment.save()

                    error_msg = iyzico_response.get('errorMessage', "Payment initialization failed.")
                    return False, error_msg

            except Exception as e:
                payment.status = 'failed'
                payment.save()

                return False, str(e)

    @staticmethod
    def complete_3d_payment(payment_id, request_data):
        """
        Complete the 3D Secure payment after bank verification.
        """
        payment = Payment.objects.get(id=payment_id)

        with transaction.atomic():
            try:
                # Complete 3D payment in Iyzico
                complete_response = iyzico_service.complete_3d_payment(request_data)

                # Check if payment was successful
                if complete_response.get('status') == 'success':
                    # Update payment status
                    payment.status = 'completed'
                    payment.iyzico_payment_id = complete_response.get('paymentId')
                    payment.save()

                    # Create a transaction record
                    Transaction.objects.create(
                        payment=payment,
                        amount=payment.amount,
                        transaction_type='payment',
                        status='succeeded',
                        transaction_id=complete_response.get('paymentId')
                    )

                    # Update booking status
                    booking = payment.booking
                    booking.status = 'confirmed'
                    booking.save()

                    return True, "Payment completed successfully."
                else:
                    payment.status = 'failed'
                    payment.save()

                    error_msg = complete_response.get('errorMessage', "3D Secure authentication failed.")
                    return False, error_msg

            except Exception as e:
                payment.status = 'failed'
                payment.save()

                return False, str(e)

    @staticmethod
    def refund_payment(payment, amount=None):
        """
        Refund a payment.
        """
        if not amount:
            amount = payment.amount

        with transaction.atomic():
            try:
                # Refund in Iyzico
                refund_result = iyzico_service.refund_payment(
                    payment_id=payment.iyzico_payment_id,
                    amount=amount if amount != payment.amount else None
                )

                # Check if refund was successful
                if refund_result.get('status') == 'success':
                    # Create a transaction record
                    Transaction.objects.create(
                        payment=payment,
                        amount=amount,
                        transaction_type='refund',
                        status='succeeded',
                        transaction_id=refund_result.get('paymentTransactionId')
                    )

                    # Update payment status
                    payment.status = 'refunded'
                    payment.save()

                    # Update booking status
                    booking = payment.booking
                    booking.status = 'cancelled'
                    booking.save()

                    return True, "Payment refunded successfully."
                else:
                    error_msg = refund_result.get('errorMessage', "Refund processing failed.")
                    return False, error_msg

            except Exception as e:
                return False, str(e)

    @staticmethod
    def release_to_traveler(payment):
        """
        Release the payment from escrow to the traveler.
        """
        with transaction.atomic():
            try:
                # Calculate platform fee
                from admin_dashboard.models import SystemSettings
                settings = SystemSettings.get_settings()
                platform_fee_percentage = settings.platform_fee_percentage
                platform_fee = payment.amount * (platform_fee_percentage / 100)

                # Amount to transfer to traveler
                transfer_amount = payment.amount - platform_fee

                # In a real implementation with Iyzico, you would use their
                # sub-merchant/marketplace API to transfer funds to the traveler

                # Create a transaction record for the escrow release
                Transaction.objects.create(
                    payment=payment,
                    amount=transfer_amount,
                    transaction_type='release',
                    status='succeeded',
                    transaction_id=f"release_{payment.iyzico_payment_id}"
                )

                return True, "Payment released to traveler successfully."

            except Exception as e:
                return False, str(e)