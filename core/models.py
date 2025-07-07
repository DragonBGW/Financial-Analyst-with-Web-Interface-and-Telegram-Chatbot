# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio  = models.TextField(blank=True)

    def __str__(self):
        return self.user.username


class Prediction(models.Model):
    user          = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker        = models.CharField(max_length=10)
    created       = models.DateTimeField(default=timezone.now)
    next_price    = models.DecimalField(max_digits=12, decimal_places=4)
    mse           = models.FloatField()
    rmse          = models.FloatField()
    r2            = models.FloatField()
    plot_closing  = models.CharField(max_length=255)
    plot_cmp      = models.CharField(max_length=255)
    metrics       = models.JSONField(default=dict)

    class Meta:
        ordering = ["-created"]
        indexes  = [models.Index(fields=["ticker", "created"])]

    def __str__(self):
        return f"{self.ticker} @ {self.created:%Y‑%m‑%d}"


class TelegramUser(models.Model):
    user    = models.OneToOneField(User, on_delete=models.CASCADE)
    chat_id = models.BigIntegerField(unique=True)

    def __str__(self):
        return f"{self.user.username} ↔️ {self.chat_id}"
