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
"""
URL configuration for stock_prediction_main project.
"""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

# Front‑end & health views
from core.views_frontend import root_redirect
from core.view_health import healthz

# Stripe / billing views
from core.views_billing import (
    subscribe_view,
    billing_success_view,
    billing_cancel_view,
)

urlpatterns = [
    # —— Billing —— -----------------------------------------------------------
    path("subscribe/",        subscribe_view,      name="subscribe"),
    path("billing/success/",  billing_success_view, name="billing-success"),
    path("billing/cancel/",   billing_cancel_view,  name="billing-cancel"),

    # —— Misc —— --------------------------------------------------------------
    path("",          root_redirect, name="root"),
    path("healthz/",  healthz,       name="healthz"),

    # —— Admin —— -------------------------------------------------------------
    path("admin/", admin.site.urls),

    # —— API —— ---------------------------------------------------------------
    path("api/v1/", include("core.urls")),
]

# ─────────────────────────────────────────────────────────────────────────────
# Serve static & media files **only** in development (DEBUG = True)
# In production use nginx, WhiteNoise, S3, etc.
# ─────────────────────────────────────────────────────────────────────────────
if settings.DEBUG:
    # /static/  (Tailwind, JS, generated plots, etc.)
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATICFILES_DIRS[0]  # BASE_DIR / "static"
    )
    # /media/   (if you ever store uploads separately)
    if hasattr(settings, "MEDIA_URL") and hasattr(settings, "MEDIA_ROOT"):
        urlpatterns += static(
            settings.MEDIA_URL,
            document_root=settings.MEDIA_ROOT
        )
