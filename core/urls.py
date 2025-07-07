from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# ---- Front‑end views ----
from .views_frontend import (
    register,
    login,
    logout,
    dashboard,
    suggest_username,     # ← import the function directly
)

# ---- API views ----
from .views import RegisterView, PredictView, PredictionListView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    # ─── API endpoints ───────────────────────────────────────────
    path("register/",          RegisterView.as_view()),
    path("token/",             TokenObtainPairView.as_view()),
    path("token/refresh/",     TokenRefreshView.as_view()),
    path("predict/",           PredictView.as_view()),
    path("predictions/",       PredictionListView.as_view()),

    # ─── Front‑end pages ────────────────────────────────────────
    path("frontend/register/",  register,          name="register"),
    path("frontend/login/",     login,             name="login"),
    path("frontend/logout/",    logout,            name="logout"),
    path("frontend/dashboard/", dashboard,         name="dashboard"),
    path("frontend/suggest-username/", suggest_username, name="suggest-username"),
]

# serve static files in development
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
