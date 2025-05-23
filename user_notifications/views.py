# user_notifications/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Notification


@login_required
def notification_list(request):
    """
    Display all notifications for the current user.
    Also mark all displayed notifications as read.
    """
    # Get all notifications for the user
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    # Mark unread notifications as read when user views the notification list
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    return render(request, 'user_notifications/notification_list.html', {
        'notifications': notifications,
    })


@require_POST
@login_required
def mark_as_read(request, notification_id):
    """
    Mark a notification as read.
    """
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    else:
        return redirect('notification_list')


@require_POST
@login_required
def mark_all_as_read(request):
    """
    Mark all notifications as read.
    """
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    else:
        return redirect('notification_list')


@login_required
def unread_count(request):
    """
    Get the count of unread notifications.
    """
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def view_notification(request, notification_id):
    """
    Mark a notification as read and redirect to its link.
    """
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()

    # Redirect to the notification's link or fallback to the notification list
    return redirect(notification.link or 'notification_list')