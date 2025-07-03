# core/urls_payment.py
from django.urls import path
from .views_payment import create_checkout, stripe_webhook

urlpatterns = [
    path("subscribe/", create_checkout, name="subscribe"),
    path("webhooks/stripe/", stripe_webhook, name="stripe_webhook"),
]
