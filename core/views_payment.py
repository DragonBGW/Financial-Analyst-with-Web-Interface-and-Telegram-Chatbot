# core/views_payment.py
import stripe
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

@require_POST
@login_required
def create_checkout(request):
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": settings.STRIPE_PRICE_ID, "quantity": 1}],
        customer_email=request.user.email,
        success_url=request.build_absolute_uri("/dashboard?pro=1"),
        cancel_url=request.build_absolute_uri("/dashboard"),
        metadata={"user_id": request.user.id},
    )
    return redirect(session.url, code=303)
