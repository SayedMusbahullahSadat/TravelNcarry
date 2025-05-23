# payments/urls.py
from django.urls import path
from . import views, webhooks

urlpatterns = [
    path('payment/<uuid:booking_id>/', views.payment_page, name='payment_page'),
    path('payment/3d-callback/', views.iyzico_3d_callback, name='iyzico_3d_callback'),
    path('payment/success/<uuid:payment_id>/', views.payment_success, name='payment_success'),
    path('payment/release/<uuid:booking_id>/', views.release_payment, name='release_payment'),
    path('payment/refund/<uuid:booking_id>/', views.cancel_and_refund, name='cancel_and_refund'),
    path('payment/history/', views.payment_history, name='payment_history'),
    path('webhook/iyzico/', webhooks.iyzico_webhook, name='iyzico_webhook'),
]