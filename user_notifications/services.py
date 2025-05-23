# user_notifications/services.py
from .models import Notification


class NotificationService:
    @staticmethod
    def create_notification(user, notification_type, title, message, link=''):
        """
        Create a new notification for a user.
        """
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link
        )
        return notification

    @staticmethod
    def create_booking_notification(booking, notification_type='booking'):
        """
        Create a notification for a booking update.
        """
        # Notify the sender
        sender_title = f"Booking {booking.get_status_display()}"
        sender_message = f"Your booking from {booking.itinerary.origin} to {booking.itinerary.destination} has been {booking.get_status_display().lower()}."
        sender_link = f"/bookings/{booking.id}/"

        NotificationService.create_notification(
            user=booking.sender,
            notification_type=notification_type,
            title=sender_title,
            message=sender_message,
            link=sender_link
        )

        # Notify the traveler
        traveler_title = f"Booking {booking.get_status_display()}"
        traveler_message = f"A booking for your itinerary from {booking.itinerary.origin} to {booking.itinerary.destination} has been {booking.get_status_display().lower()}."
        traveler_link = f"/bookings/{booking.id}/"

        NotificationService.create_notification(
            user=booking.itinerary.traveler,
            notification_type=notification_type,
            title=traveler_title,
            message=traveler_message,
            link=traveler_link
        )

    @staticmethod
    def create_payment_notification(payment, notification_type='payment'):
        """
        Create a notification for a payment update.
        """
        # Notify the sender
        sender_title = f"Payment {payment.get_status_display()}"
        sender_message = f"Your payment of ${payment.amount} for booking has been {payment.get_status_display().lower()}."
        sender_link = f"/bookings/{payment.booking.id}/"

        NotificationService.create_notification(
            user=payment.booking.sender,
            notification_type=notification_type,
            title=sender_title,
            message=sender_message,
            link=sender_link
        )

        # Notify the traveler
        traveler_title = f"Payment {payment.get_status_display()}"
        traveler_message = f"Payment of ${payment.amount} for booking has been {payment.get_status_display().lower()}."
        traveler_link = f"/bookings/{payment.booking.id}/"

        NotificationService.create_notification(
            user=payment.booking.itinerary.traveler,
            notification_type=notification_type,
            title=traveler_title,
            message=traveler_message,
            link=traveler_link
        )

    @staticmethod
    def create_message_notification(message, notification_type='message'):
        """
        Create a notification for a new message.
        """
        # Get the recipient (the other user in the conversation)
        recipient = message.conversation.get_other_participant(message.sender)

        title = f"New message from {message.sender.username}"
        message_preview = message.content[:50] + ('...' if len(message.content) > 50 else '')
        link = f"/messages/conversation/{message.conversation.id}/"

        NotificationService.create_notification(
            user=recipient,
            notification_type=notification_type,
            title=title,
            message=message_preview,
            link=link
        )

    @staticmethod
    def create_rating_notification(rating, notification_type='rating'):
        """
        Create a notification for a new rating.
        """
        title = f"New {rating.rating}-star rating from {rating.from_user.username}"
        message = f"You've received a new rating for a booking."
        link = f"/profile/{rating.to_user.id}/"

        NotificationService.create_notification(
            user=rating.to_user,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link
        )