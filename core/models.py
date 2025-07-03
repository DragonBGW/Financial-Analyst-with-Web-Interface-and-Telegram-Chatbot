from django.db import models

# Create your models here.
# core/models.py
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.timezone import now, localdate
from django.db.models import JSONField  # for Postgres; fallback to models.JSONField in SQLite

# core/models.py (excerpt)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_pro = models.BooleanField(default=False)


class UserProfile(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE)
    is_pro     = models.BooleanField(default=False)
    # quota counters
    date       = models.DateField(default=localdate)
    daily_used = models.PositiveIntegerField(default=0)

    def inc_usage(self):
        today = localdate()
        if self.date != today:
            self.date, self.daily_used = today, 0
        self.daily_used += 1
        self.save()


class Prediction(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker       = models.CharField(max_length=10)
    created      = models.DateTimeField(default=timezone.now)
    next_price   = models.DecimalField(max_digits=12, decimal_places=4)
    mse          = models.FloatField()
    rmse         = models.FloatField()
    r2           = models.FloatField()
    plot_closing = models.FilePathField(path="static/plots", null=True, blank=True)
    plot_cmp     = models.FilePathField(path="static/plots", null=True, blank=True)
    metrics      = models.JSONField(default=dict)  # stores extra info

    class Meta:
        ordering = ["-created"]
        indexes  = [models.Index(fields=["ticker", "created"])]


from django.db import models
from django.contrib.auth.models import User

class TelegramUser(models.Model):
    user     = models.OneToOneField(User, on_delete=models.CASCADE)
    chat_id  = models.BigIntegerField(unique=True)

    def __str__(self):
        return f"{self.user.username} ↔️ {self.chat_id}"

