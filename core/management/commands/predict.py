from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from core.utils import run_prediction
from core.models import Prediction

User = get_user_model()

class Command(BaseCommand):
    help = "Run stock‑price prediction for a single ticker or all tickers."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--ticker", type=str, help="Single ticker symbol (e.g. TSLA)"
        )
        group.add_argument(
            "--all", action="store_true", help="Run for every unique ticker in Prediction table"
        )
        parser.add_argument(
            "--user", type=str, default=None,
            help="Username to own the predictions (default: first superuser)"
        )

    def handle(self, *args, **options):
        # Pick the user that will own the prediction records
        if options["user"]:
            try:
                user = User.objects.get(username=options["user"])
            except User.DoesNotExist:
                raise CommandError(f"User '{options['user']}' not found")
        else:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                raise CommandError("No superuser found; create one or pass --user")

        tickers = []
        if options["ticker"]:
            tickers = [options["ticker"]]
        elif options["all"]:
            tickers = (
                Prediction.objects.values_list("ticker", flat=True)
                .distinct()
                .order_by("ticker")
            )
            if not tickers:
                raise CommandError("No existing tickers in DB; use --ticker first")

        for t in tickers:
            self.stdout.write(f"Predicting {t} …", ending="")
            try:
                pred = run_prediction(user, t)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f" failed: {e}"))
                continue
            self.stdout.write(self.style.SUCCESS(" done"))
            self.stdout.write(
                f" → {t}: {pred.next_price}  (mse {pred.mse:.4e}, rmse {pred.rmse:.4f})"
            )
