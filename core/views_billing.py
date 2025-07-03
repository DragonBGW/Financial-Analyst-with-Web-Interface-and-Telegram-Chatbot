# core/views_billing.py
import stripe, json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

# ─── Stripe configuration ─────────────────────────────────────────
stripe.api_key = settings.STRIPE_SECRET_KEY        # secret key from .env

STRIPE_PUBLIC_KEY = settings.STRIPE_PUBLIC_KEY
STRIPE_PRICE_ID   = settings.STRIPE_PRICE_ID       # e.g. "price_12345"

# ─── /subscribe/ ──────────────────────────────────────────────────
@login_required
def subscribe_view(request):
    """
    GET  → render pricing page
    POST → create Stripe Checkout Session and redirect
    """
    if request.method == "POST":
        # Create a subscription‑mode checkout session
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            customer_email=request.user.email or None,
            line_items=[
                {"price": STRIPE_PRICE_ID, "quantity": 1}
            ],
            success_url=request.build_absolute_uri("/billing/success/"),
            cancel_url=request.build_absolute_uri("/billing/cancel/"),
        )
        return redirect(session.url)          # Stripe hosted page

    # GET → show the Subscribe button
    context = {
        "stripe_pk": STRIPE_PUBLIC_KEY,
        "price_id":   STRIPE_PRICE_ID,
    }
    return render(request, "billing/subscribe.html", context)


# ─── /billing/success/  (temporary activation) ────────────────────
@login_required
def billing_success_view(request):
    """
    Temporary: mark the user as Pro immediately after redirect.
    In production you'll switch to webhook‑driven activation.
    """
    profile = request.user.userprofile
    profile.is_pro = True
    profile.save()
    return render(request, "billing/success.html")


# ─── /billing/cancel/ ─────────────────────────────────────────────
@login_required
def billing_cancel_view(request):
    return render(request, "billing/cancel.html")


# ─── /webhooks/stripe/ (stub for later) ───────────────────────────
@csrf_exempt
def stripe_webhook_view(request):
    """
    Stub: accept POSTs from Stripe but ignore them for now.
    When you’re ready for prod, uncomment the code to verify
    signatures and update subscription status automatically.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Method not allowed")

    # ── Uncomment when you enable real webhooks ───────────
    # payload     = request.body
    # sig_header  = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    # try:
    #     event = stripe.Webhook.construct_event(
    #         payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    #     )
    # except ValueError:
    #     return HttpResponseBadRequest("Invalid payload")
    # except stripe.error.SignatureVerificationError:
    #     return HttpResponseBadRequest("Invalid signature")
    #
    # # Handle relevant events, e.g. subscription cancelled
    # if event["type"] == "customer.subscription.deleted":
    #     email = event["data"]["object"].get("customer_email")
    #     if email:
    #         User.objects.filter(email=email).update(
    #             userprofile__is_pro=False
    #         )

    return JsonResponse({"status": "ignored (webhook stubbed)"})
