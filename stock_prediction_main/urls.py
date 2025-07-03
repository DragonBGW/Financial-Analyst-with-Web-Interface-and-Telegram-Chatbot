"""
URL configuration for stock_prediction_main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

# If you defined root_redirect in core/views_frontend.py
from core.views_frontend import root_redirect
from core.view_health import healthz
# ─── New billing / Stripe views ───────────────────
from core.views_billing import (
    subscribe_view,            # GET ⇒ show plans page / POST ⇒ create CheckoutSession
    billing_success_view,      # GET  ⇒ success redirect
    billing_cancel_view,       # GET  ⇒ cancel redirect
)


urlpatterns = [

    # Billing routes  (put them high so they’re easy to spot)
    path("subscribe/",     subscribe_view,     name="subscribe"),
    path("billing/success/", billing_success_view, name="billing-success"),
    path("billing/cancel/",  billing_cancel_view,  name="billing-cancel"),
    
    # Root URL → dashboard (or login) via redirect
    path("", root_redirect, name="root"),         

    path("healthz/", healthz, name="healthz"),      #  ← critical endpoint

    # Django admin
    path("admin/", admin.site.urls),

    # All API + frontend routes that live in core/urls.py
    path("api/v1/", include("core.urls")),
]

# Serve uploaded plots in development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
