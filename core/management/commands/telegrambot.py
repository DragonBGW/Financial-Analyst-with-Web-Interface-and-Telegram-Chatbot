# core/management/commands/telegrambot.py
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from core.models import TelegramUser, Prediction
from core.utils import run_prediction
from core.tg_rate import too_many_calls
import asyncio
import functools
import os

BOT_TOKEN = settings.BOT_TOKEN

# ─── Async ORM + blocking wrappers ────────────────────────────────

@sync_to_async
def link_telegram_user(chat_id: int, username: str):
    user, _ = User.objects.get_or_create(username=username or f"tg_{chat_id}")
    return TelegramUser.objects.get_or_create(chat_id=chat_id, defaults={"user": user})

@sync_to_async(thread_sensitive=False)
def run_prediction_threadsafe(user, ticker: str):
    return run_prediction(user, ticker)

@sync_to_async
def get_latest_prediction(user):
    return Prediction.objects.filter(user=user).order_by("-created").first()

def open_input_file(path: str) -> InputFile:
    return InputFile(os.path.join(settings.BASE_DIR, path))

# ─── Command ──────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Run Telegram bot"

    def handle(self, *args, **kwargs):
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("help", self.help))
        app.add_handler(CommandHandler("predict", self.predict))
        app.add_handler(CommandHandler("latest", self.latest))
        self.stdout.write(self.style.SUCCESS("🤖 Bot is polling…"))
        app.run_polling()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        username = update.effective_user.username or ""
        await link_telegram_user(chat_id, username)

        await update.message.reply_text(
            "Welcome to Stock Insight Bot!\nUse /predict <TICKER> to get tomorrow’s price."
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("/predict <TICKER> → forecast\n/latest → most recent prediction")

    async def predict(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        username = update.effective_user.username or ""
        telegram_user, _ = await link_telegram_user(chat_id, username)

        if too_many_calls(chat_id):
            await update.message.reply_text("Rate limit: max 10 predictions/min.")
            return

        if not context.args:
            await update.message.reply_text("Usage: /predict TSLA")
            return

        ticker = context.args[0].upper()
        await update.message.reply_text(f"🔮 Predicting {ticker} …")

        try:
            pred = await run_prediction_threadsafe(telegram_user.user, ticker)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            return

        # Send photos and summary
        try:
            closing_img = open_input_file(pred.plot_closing)
            cmp_img = open_input_file(pred.plot_cmp)
            await update.message.reply_photo(closing_img)
            await update.message.reply_photo(cmp_img)

            msg = f"*{ticker}* → *{pred.next_price:.2f}*\nR²={pred.r2:.3f}, RMSE={pred.rmse:.4f}"
            await update.message.reply_markdown(msg)
        except Exception as e:
            await update.message.reply_text(f"⚠️ Failed to send image: {e}")

    async def latest(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        username = update.effective_user.username or ""
        telegram_user, _ = await link_telegram_user(chat_id, username)

        pred = await get_latest_prediction(telegram_user.user)
        if not pred:
            await update.message.reply_text("No predictions yet.")
            return

        try:
            cmp_img = open_input_file(pred.plot_cmp)
            await update.message.reply_photo(cmp_img)

            msg = (
                f"*{pred.ticker}* → *{pred.next_price:.2f}*\n"
                f"{pred.created:%Y-%m-%d %H:%M}\nR²={pred.r2:.3f}, RMSE={pred.rmse:.4f}"
            )
            await update.message.reply_markdown(msg)
        except Exception as e:
            await update.message.reply_text(f"⚠️ Failed to load prediction: {e}")
