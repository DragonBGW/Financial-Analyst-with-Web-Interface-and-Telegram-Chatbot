"""
Telegram bot management command for Stock‑Insight.
"""

from __future__ import annotations          # ← must be FIRST

import asyncio
import logging
import os
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from asgiref.sync import sync_to_async
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.error import BadRequest
from telegram.helpers import escape_markdown

from core.models import TelegramUser, Prediction
from core.utils import run_prediction_async
from core.tg_rate import too_many_calls

BOT_TOKEN = settings.BOT_TOKEN
logger = logging.getLogger(__name__)

# ────────────────────────── Async‑ORM helpers ────────────────────────────────
@sync_to_async
def link_telegram_user(chat_id: int, username: str) -> tuple[User, bool]:
    user, _ = User.objects.get_or_create(username=username or f"tg_{chat_id}")
    tg_user, created = TelegramUser.objects.get_or_create(
        chat_id=chat_id,
        defaults={"user": user},
    )
    return tg_user.user, created


@sync_to_async
def get_latest_user_prediction(user: User) -> Optional[Prediction]:
    return (
        Prediction.objects.filter(user=user)
        .select_related("user")
        .order_by("-created")
        .first()
    )

# ─────────────────────── File / image helpers ────────────────────────────────
async def open_input_file(path: str) -> InputFile:
    full_path = os.path.join(settings.BASE_DIR, path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Image not found: {full_path}")
    if os.path.getsize(full_path) == 0:
        raise ValueError(f"Empty image file: {full_path}")

    loop = asyncio.get_event_loop()
    with open(full_path, "rb") as f:
        buf = await loop.run_in_executor(None, f.read)
    return InputFile(buf, filename=os.path.basename(full_path))


async def send_image_safely(update: Update, img_path: str, caption: str = "") -> bool:
    try:
        img = await open_input_file(img_path)
        await update.message.reply_photo(img, caption=caption)
        return True
    except BadRequest as e:
        logger.error("Telegram rejected %s: %s", img_path, e)
    except Exception as e:
        logger.error("Failed to send %s: %s", img_path, e)
    return False

# ───────────────────────────── Bot command ───────────────────────────────────
class Command(BaseCommand):
    help = "Run Telegram bot"

    # entry point
    def handle(self, *args, **options):
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("help", self.help))
        app.add_handler(CommandHandler("predict", self.predict))
        app.add_handler(CommandHandler("latest", self.latest))
        app.add_error_handler(self.error_handler)

        self.stdout.write(self.style.SUCCESS("🤖 Bot is polling..."))
        app.run_polling()

    # global error handler
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.error("Update %s caused error: %s", update, context.error)
        if getattr(update, "message", None):
            await update.message.reply_text("⚠️ An error occurred. Please try again later.")

    # /start
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        username = update.effective_user.username or ""
        await link_telegram_user(chat_id, username)
        await update.message.reply_text(
            "📈 Welcome to Stock Insight Bot!\n\n"
            "/predict <TICKER> – Get tomorrow's price prediction\n"
            "/latest – Show your most recent prediction\n"
            "/help – Show help"
        )

    # /help
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "ℹ️ Commands:\n"
            "/predict <TICKER> – Predict price (e.g., /predict AAPL)\n"
            "/latest – Show your most recent prediction"
        )

    # /predict
    async def predict(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        username = update.effective_user.username or ""

        try:
            user, _ = await link_telegram_user(chat_id, username)

            if await sync_to_async(too_many_calls)(chat_id):
                await update.message.reply_text("⏳ Rate limit: 10 predictions per minute.")
                return

            if not context.args:
                await update.message.reply_text("Usage: /predict <TICKER>")
                return

            ticker = context.args[0].upper()
            await update.message.reply_text(f"🔍 Analyzing {ticker}…")

            pred = await run_prediction_async(user, ticker)

            # send images
            images_sent = 0
            if pred.plot_closing and await send_image_safely(update, pred.plot_closing, f"{ticker} Price History"):
                images_sent += 1
            if pred.plot_cmp and await send_image_safely(update, pred.plot_cmp, f"{ticker} Prediction Comparison"):
                images_sent += 1

            # prediction summary (escape all special chars, avoid '=')
            result_msg = (
                f"📊 *{escape_markdown(ticker, 2)} Prediction*\n\n"
                f"➡️ Next Price: *${escape_markdown(f'{pred.next_price:.2f}', 2)}*\n"
                f"📈 Accuracy: R² {escape_markdown(f'{pred.r2:.3f}', 2)}, "
                f"RMSE {escape_markdown(f'{pred.rmse:.4f}', 2)}\n\n"
                f"{'🖼️ ' if images_sent else '⚠️ '}{images_sent}/2 charts shown"
            )
            await update.message.reply_markdown_v2(result_msg)

        except ValueError as e:
            await update.message.reply_text(f"❌ {e}")
        except Exception:
            logger.exception("Prediction failed for %s", chat_id)
            await update.message.reply_text("🚨 Prediction failed. Please try again later.")

    # /latest
    async def latest(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        username = update.effective_user.username or ""

        try:
            user, _ = await link_telegram_user(chat_id, username)
            pred = await get_latest_user_prediction(user)
            if not pred:
                await update.message.reply_text("No predictions yet. Use /predict first.")
                return

            image_sent = False
            if pred.plot_cmp:
                image_sent = await send_image_safely(update, pred.plot_cmp, f"Latest {pred.ticker} Prediction")

            latest_msg = (
                f"⏱️ *Your Latest Prediction*\n\n"
                f"🏷️ Ticker: *{escape_markdown(pred.ticker, 2)}*\n"
                f"📅 Date: {escape_markdown(pred.created.strftime('%Y-%m-%d %H:%M'), 2)}\n\n"
                f"💰 Price: *${escape_markdown(f'{pred.next_price:.2f}', 2)}*\n"
                f"📊 Accuracy: R² {escape_markdown(f'{pred.r2:.3f}', 2)}, "
                f"RMSE {escape_markdown(f'{pred.rmse:.4f}', 2)}\n\n"
                f"{'🖼️ Chart attached' if image_sent else '⚠️ Chart unavailable'}"
            )

            await update.message.reply_markdown_v2(latest_msg)

        except Exception:
            logger.exception("Latest prediction failed for %s", chat_id)
            await update.message.reply_text("⚠️ Failed to load your latest prediction.")
