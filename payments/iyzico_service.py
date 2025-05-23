# payments/iyzico_service.py
import iyzipay
from django.conf import settings
import uuid
from django.urls import reverse
from django.contrib.sites.models import Site


class IyzicoService:
    """
    Implementation of Iyzico payment service
    """

    def __init__(self):
        self.options = {
            'api_key': settings.IYZICO_API_KEY,
            'secret_key': settings.IYZICO_SECRET_KEY,
            'base_url': settings.IYZICO_BASE_URL
        }

    def create_payment(self, buyer, booking, card_info):
        """Create a payment with Iyzico"""

        # Create a unique payment request
        request = {
            'locale': 'en',
            'conversationId': str(booking.id),
            'price': str(booking.price),
            'paidPrice': str(booking.price),
            'currency': 'TRY',  # Turkish Lira - adjust as needed
            'installment': '1',
            'basketId': str(booking.id),
            'paymentChannel': 'WEB',
            'paymentGroup': 'PRODUCT',

            # Card information
            'paymentCard': {
                'cardHolderName': card_info['name_on_card'],
                'cardNumber': card_info['card_number'].replace(' ', ''),
                'expireMonth': card_info['expiry_month'],
                'expireYear': card_info['expiry_year'],
                'cvc': card_info['cvc'],
                'registerCard': '0'
            },

            # Buyer information
            'buyer': {
                'id': str(buyer.id),
                'name': buyer.first_name,
                'surname': buyer.last_name,
                'gsmNumber': buyer.phone_number,
                'email': buyer.email,
                'identityNumber': '11111111111',  # Required in Turkey
                'registrationAddress': buyer.address or 'Not provided',
                'ip': '85.34.78.112',  # Should be actual client IP
                'city': 'Istanbul',  # Should be actual city
                'country': 'Turkey',  # Should be actual country
                'zipCode': '34732'  # Should be actual zip code
            },

            # Shipping address
            'shippingAddress': {
                'contactName': buyer.get_full_name() or buyer.username,
                'city': 'Istanbul',
                'country': 'Turkey',
                'address': buyer.address or 'Not provided',
                'zipCode': '34742'
            },

            # Billing address
            'billingAddress': {
                'contactName': buyer.get_full_name() or buyer.username,
                'city': 'Istanbul',
                'country': 'Turkey',
                'address': buyer.address or 'Not provided',
                'zipCode': '34742'
            },

            # Basket items
            'basketItems': [
                {
                    'id': 'PACKAGE-' + str(booking.id),
                    'name': f'Package Delivery: {booking.itinerary.origin} to {booking.itinerary.destination}',
                    'category1': 'Package',
                    'itemType': 'VIRTUAL',
                    'price': str(booking.price)
                }
            ]
        }

        # Make the request to Iyzico
        payment = iyzipay.Payment().create(request, self.options)

        return payment

    def create_3d_payment(self, buyer, booking, card_info, request):
        """Create a 3D secure payment with Iyzico"""

        # Get the domain for callback URL
        current_site = Site.objects.get_current()
        domain = current_site.domain
        scheme = 'https' if request.is_secure() else 'http'

        # Create callback URLs
        callback_url = f"{scheme}://{domain}{reverse('iyzico_3d_callback')}"

        # Create a unique payment request
        request_data = {
            'locale': 'en',
            'conversationId': str(booking.id),
            'price': str(booking.price),
            'paidPrice': str(booking.price),
            'currency': 'TRY',  # Turkish Lira - adjust as needed
            'installment': '1',
            'basketId': str(booking.id),
            'paymentChannel': 'WEB',
            'paymentGroup': 'PRODUCT',
            'callbackUrl': callback_url,

            # Card information
            'paymentCard': {
                'cardHolderName': card_info['name_on_card'],
                'cardNumber': card_info['card_number'].replace(' ', ''),
                'expireMonth': card_info['expiry_month'],
                'expireYear': card_info['expiry_year'],
                'cvc': card_info['cvc'],
                'registerCard': '0'
            },

            # Buyer information
            'buyer': {
                'id': str(buyer.id),
                'name': buyer.first_name or buyer.username,
                'surname': buyer.last_name or 'User',
                'gsmNumber': buyer.phone_number or '+905350000000',
                'email': buyer.email,
                'identityNumber': '11111111111',  # Required in Turkey
                'registrationAddress': buyer.address or 'Not provided',
                'ip': request.META.get('REMOTE_ADDR', '127.0.0.1'),
                'city': 'Istanbul',  # Should be actual city
                'country': 'Turkey',  # Should be actual country
                'zipCode': '34732'  # Should be actual zip code
            },

            # Shipping address
            'shippingAddress': {
                'contactName': buyer.get_full_name() or buyer.username,
                'city': 'Istanbul',
                'country': 'Turkey',
                'address': buyer.address or 'Not provided',
                'zipCode': '34742'
            },

            # Billing address
            'billingAddress': {
                'contactName': buyer.get_full_name() or buyer.username,
                'city': 'Istanbul',
                'country': 'Turkey',
                'address': buyer.address or 'Not provided',
                'zipCode': '34742'
            },

            # Basket items
            'basketItems': [
                {
                    'id': 'PACKAGE-' + str(booking.id),
                    'name': f'Package Delivery: {booking.itinerary.origin} to {booking.itinerary.destination}',
                    'category1': 'Package',
                    'itemType': 'VIRTUAL',
                    'price': str(booking.price)
                }
            ]
        }

        # Make the request to Iyzico
        three_d_s_initialize = iyzipay.ThreedsInitialize().create(request_data, self.options)

        return three_d_s_initialize

    def retrieve_payment(self, payment_id):
        """Retrieve a payment from Iyzico"""
        request = {
            'locale': 'en',
            'conversationId': str(uuid.uuid4()),
            'paymentId': payment_id
        }

        payment = iyzipay.Payment().retrieve(request, self.options)
        return payment

    def refund_payment(self, payment_id, amount=None):
        """Refund a payment in Iyzico"""
        request = {
            'locale': 'en',
            'conversationId': str(uuid.uuid4()),
            'paymentTransactionId': payment_id,
        }

        if amount:
            request['price'] = str(amount)
            refund = iyzipay.Refund().create(request, self.options)
        else:
            refund = iyzipay.Cancel().create(request, self.options)

        return refund

    def complete_3d_payment(self, request_data):
        """Complete a 3D secure payment after bank verification"""
        return iyzipay.ThreedsPayment().create(request_data, self.options)


# Create a singleton instance
iyzico_service = IyzicoService()