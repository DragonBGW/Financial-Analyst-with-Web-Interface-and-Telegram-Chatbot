# core/views_frontend.py
from __future__ import annotations

import uuid

from django.contrib.auth import (
    login as auth_login,
    logout as auth_logout,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET

from rest_framework_simplejwt.tokens import RefreshToken


# ─────────────────────────── Username generator ──────────────────────────────
def generate_unique_username() -> str:
    """
    Generate a username like 'user_a1b2c3' that is guaranteed unique.
    """
    while True:
        candidate = "user_" + uuid.uuid4().hex[:6]
        if not User.objects.filter(username=candidate).exists():
            return candidate


@require_GET
def suggest_username(request):
    """
    AJAX endpoint: returns {"username": "<unique>"}.
    """
    return JsonResponse({"username": generate_unique_username()})


# ─────────────────────────── Auth views (HTML) ───────────────────────────────
def register(request):
    if request.method == "POST":
        # If user left username blank (e.g. they relied on the Suggest button),
        # inject a unique one so form validation passes.
        post_data = request.POST.copy()
        if not post_data.get("username"):
            post_data["username"] = generate_unique_username()

        form = UserCreationForm(post_data)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)                     # auto‑login
            return redirect("dashboard")
    else:
        form = UserCreationForm()

    return render(request, "register.html", {"form": form})


def login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)

            # Issue JWT for JS → API calls
            refresh = RefreshToken.for_user(user)
            request.session["access_token"]  = str(refresh.access_token)
            request.session["refresh_token"] = str(refresh)

            return redirect("dashboard")
    else:
        form = AuthenticationForm()

    return render(request, "login.html", {"form": form})


def logout(request):
    auth_logout(request)
    return redirect("login")


def root_redirect(request):
    return redirect("dashboard")


def healthz(request):
    return HttpResponse("ok")


@login_required
def dashboard(request):
    context = {"access_token": request.session.get("access_token")}
    return render(request, "dashboard.html", context)
