from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from rest_framework_simplejwt.tokens import RefreshToken

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)   # log them in directly
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

            # create JWT tokens so JS can call the API
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

from django.shortcuts import redirect
def root_redirect(request):
    return redirect("dashboard")   # or "login"

from django.http import HttpResponse

def healthz(request):
    return HttpResponse("ok")

@login_required
def dashboard(request):
    context = {"access_token": request.session.get("access_token")}
    return render(request, "dashboard.html", context)
