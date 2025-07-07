# core/utils.py
"""
Async utilities for downloading data, running the LSTM model, generating
plots, and persisting a Prediction row.
"""

from __future__ import annotations

import asyncio
import os
import threading
import time
import uuid
from decimal import Decimal
from typing import Dict, Tuple

import matplotlib
matplotlib.use("Agg")                     # headless backend for servers
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import yfinance as yf
from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler

from .models import Prediction

# ─── Globals ─────────────────────────────────────────────────────
MODEL_PATH = os.getenv("MODEL_PATH", "stock_prediction_model.keras")
_THREAD_LOCAL = threading.local()

# ─── Model cache helper ──────────────────────────────────────────
@sync_to_async
def get_model_async():
    """Load & cache the Keras model once per thread."""
    if not hasattr(_THREAD_LOCAL, "model"):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
        _THREAD_LOCAL.model = load_model(MODEL_PATH)
    return _THREAD_LOCAL.model


# ─── Robust Yahoo Finance downloader ─────────────────────────────
def safe_yf_download(
    ticker: str,
    period: str = "10y",
    interval: str = "1d",
    max_retries: int = 5,
    backoff: float = 3.0,
) -> "pd.DataFrame":
    """
    Download data with retries and handle HTTP‑429 rate limits gracefully.
    Falls back to a manual API call if yfinance keeps failing.
    """
    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            df = yf.download(
                ticker,
                period=period,
                interval=interval,
                progress=False,
                threads=False,   # avoid double‑calling Yahoo
            )
            if not df.empty:
                return df
            last_err = ValueError("No data returned from yfinance")
        except Exception as exc:
            last_err = exc

        # Detect HTTP‑429 Too‑Many‑Requests
        if isinstance(last_err, requests.HTTPError) and last_err.response.status_code == 429:
            wait = backoff * attempt
            print(f"[safe_yf_download] 429 rate‑limited; sleeping {wait}s (attempt {attempt}/{max_retries})")
            time.sleep(wait)
        else:
            time.sleep(backoff)

    # ── Fallback to raw Yahoo Finance API ────────────────────────
    print("[safe_yf_download] Falling back to direct Yahoo API")
    return fetch_yahoo_direct(ticker)


def fetch_yahoo_direct(ticker: str) -> "pd.DataFrame":
    """
    Fetch 1‑day, 1‑minute price data using Yahoo's public chart API.
    This approach works even when yfinance is rate‑limited.
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=1d&interval=1m"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "Connection": "keep-alive",
    }

    res = requests.get(url, headers=headers, timeout=10)
    res.raise_for_status()
    data = res.json()

    try:
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]
    except (KeyError, IndexError) as e:
        raise ValueError(f"Unexpected response structure for {ticker}") from e

    if not timestamps or not closes:
        raise ValueError(f"No intraday data returned for {ticker}")

    df = pd.DataFrame(
        {
            "Datetime": pd.to_datetime(timestamps, unit="s"),
            "Close": closes,
        }
    ).set_index("Datetime")
    df = df.dropna()

    return df


# ─── Async plot helpers ──────────────────────────────────────────
async def save_plot_async(fig: "plt.Figure", path: str) -> None:
    """Save a Matplotlib figure off the main loop, then close it."""
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, lambda: fig.savefig(path, dpi=100, bbox_inches="tight"))
    finally:
        plt.close(fig)


async def create_prediction_async(user, prediction_data: Dict) -> Prediction:
    """Insert the row with a guaranteed non‑null user FK."""
    prediction_data["user"] = user
    return await sync_to_async(Prediction.objects.create)(**prediction_data)


# ─── Main async predictor ───────────────────────────────────────
async def run_prediction_async(user, ticker: str) -> Prediction:
    closing_path = cmp_path = None
    plot_dir = os.path.join(settings.BASE_DIR, "static", "plots")
    os.makedirs(plot_dir, exist_ok=True)

    uid = uuid.uuid4()
    window = 60
    loop = asyncio.get_event_loop()

    try:
        # 1 · download data
        df = await loop.run_in_executor(None, lambda: safe_yf_download(ticker))
        if len(df) < window:
            raise ValueError(f"Need ≥{window} daily points for {ticker}")

        # 2 · scale & window (CPU‑bound)
        def prepare_data() -> Tuple[MinMaxScaler, np.ndarray, np.ndarray]:
            prices = df["Close"].values.reshape(-1, 1)
            scaler = MinMaxScaler()
            scaled = scaler.fit_transform(prices)
            x_test = scaled[-window:].reshape(1, window, 1)
            return scaler, scaled, x_test

        scaler, scaled, x_test = await loop.run_in_executor(None, prepare_data)

        # 3 · predict
        model = await get_model_async()
        pred_scaled = await loop.run_in_executor(None, lambda: model.predict(x_test, verbose=0)[0][0])
        pred_price = scaler.inverse_transform([[pred_scaled]])[0][0]

        # 4 · metrics
        mse = float(np.mean((scaled[-1] - pred_scaled) ** 2))
        rmse = float(np.sqrt(mse))
        r2 = float(1 - mse / np.var(scaled[-window:]))

        # 5 · output paths
        closing_path = os.path.join(plot_dir, f"{uid}_close.png")
        cmp_path = os.path.join(plot_dir, f"{uid}_cmp.png")

        # 6 · build figures
        def create_figures():
            # ── Figure 1 · Price history ───────────────────────
            fig1 = plt.figure(figsize=(10, 6))
            ax1 = fig1.add_subplot(111)
            ax1.plot(
                df.index,
                df["Close"],
                linewidth=2,
                label="Close",
            )
            ax1.set_title(f"{ticker} Close Price History")
            ax1.set_xlabel("Date")
            ax1.set_ylabel("Price ($)")
            ax1.grid(alpha=0.3)
            fig1.autofmt_xdate()

            # ── Figure 2 · Last 60 days vs prediction ─────────
            fig2 = plt.figure(figsize=(10, 6))
            ax2 = fig2.add_subplot(111)
            last_actual = scaler.inverse_transform(scaled[-window:])
            dates = pd.date_range(end=df.index[-1], periods=window)
            ax2.plot(
                dates,
                last_actual.flatten(),
                linewidth=2,
                label="Actual",
            )
            ax2.scatter(
                df.index[-1] + pd.Timedelta(days=1),
                pred_price,
                s=100,
                label="Predicted",
                zorder=5,
            )
            ax2.set_title(f"{ticker} – Last {window} Days vs Prediction")
            ax2.legend()
            ax2.grid(alpha=0.3)
            fig2.autofmt_xdate()

            return fig1, fig2

        fig1, fig2 = await loop.run_in_executor(None, create_figures)
        await asyncio.gather(
            save_plot_async(fig1, closing_path),
            save_plot_async(fig2, cmp_path),
        )

        # 7 · save Prediction row
        prediction = await create_prediction_async(
            user,
            {
                "ticker": ticker.upper(),
                "next_price": Decimal(str(round(pred_price, 4))),
                "mse": mse,
                "rmse": rmse,
                "r2": r2,
                "plot_closing": os.path.relpath(closing_path, settings.BASE_DIR),
                "plot_cmp": os.path.relpath(cmp_path, settings.BASE_DIR),
                "metrics": {"window": window, "data_points": len(df)},
            },
        )
        return prediction

    except Exception:
        # cleanup orphaned files if any step fails
        def cleanup():
            for p in (closing_path, cmp_path):
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass

        await loop.run_in_executor(None, cleanup)
        raise


# ─── Sync wrapper for legacy code ───────────────────────────────
def run_prediction(user, ticker: str) -> Prediction:
    """Call the async pipeline from synchronous code."""
    return async_to_sync(run_prediction_async)(user, ticker)
