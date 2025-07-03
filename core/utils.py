# core/utils.py
import os, uuid, numpy as np, pandas as pd, yfinance as yf
import matplotlib
matplotlib.use("Agg")                     # headless backend
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model
from decimal import Decimal
from django.conf import settings
from .models import Prediction
import threading

MODEL_PATH = os.getenv("MODEL_PATH", "stock_prediction_model.keras")
_thread_local = threading.local()

# ─── Helpers ──────────────────────────────────────────────────────
def get_model():
    if not hasattr(_thread_local, "model"):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
        _thread_local.model = load_model(MODEL_PATH)
    return _thread_local.model

# ─── Main predictor ───────────────────────────────────────────────
def run_prediction(user, ticker: str):
    closing_path = cmp_path = None  # ✅ pre‑declare to avoid undefined refs

    try:
        # 1. Download data
        df = yf.download(ticker, period="10y", interval="1d")
        if df.empty:
            raise ValueError(f"No data for ticker {ticker}")

        # 2. Prepare window
        close_prices = df["Close"].values.reshape(-1, 1)
        scaler = MinMaxScaler()
        scaled = scaler.fit_transform(close_prices)

        window = 60
        if len(scaled) < window:
            raise ValueError(f"Not enough data for {ticker}. Need ≥{window} days.")

        X_test = scaled[-window:].reshape(1, window, 1)
        model  = get_model()
        pred_scaled = model.predict(X_test, verbose=0)[0][0]
        pred_price  = scaler.inverse_transform([[pred_scaled]])[0][0]

        # 3. Metrics
        mse  = float(np.mean((scaled[-1] - pred_scaled) ** 2))
        rmse = float(np.sqrt(mse))
        r2   = float(1 - mse / np.var(scaled[-window:]))

        # 4. Plot paths
        plot_dir = os.path.join(settings.BASE_DIR, "static", "plots")
        os.makedirs(plot_dir, exist_ok=True)
        uid = uuid.uuid4()
        closing_path = os.path.join(plot_dir, f"{uid}_close.png")
        cmp_path     = os.path.join(plot_dir, f"{uid}_cmp.png")

        # 5. Plot 1 – closing history
        plt.figure(figsize=(10, 6))
        df["Close"].plot(title=f"{ticker} Close Price History")
        plt.xlabel("Date")
        plt.ylabel("Price ($)")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(closing_path, dpi=100, bbox_inches="tight")
        plt.close()

        # 6. Plot 2 – last 60 vs prediction
        plt.figure(figsize=(10, 6))
        last_actual = scaler.inverse_transform(scaled[-window:])
        dates = pd.date_range(end=df.index[-1], periods=window)

        plt.plot(dates, last_actual.flatten(), label="Actual", linewidth=2)
        plt.scatter(df.index[-1] + pd.Timedelta(days=1), pred_price,
                    color="red", s=100, label="Predicted", zorder=5)
        plt.xlabel("Date")
        plt.ylabel("Price ($)")
        plt.title(f"{ticker} – Last {window} Days vs Prediction")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(cmp_path, dpi=100, bbox_inches="tight")
        plt.close()

        # 7. Save prediction to DB
        prediction = Prediction.objects.create(
            user=user,
            ticker=ticker.upper(),
            next_price=Decimal(str(round(pred_price, 4))),
            mse=mse,
            rmse=rmse,
            r2=r2,
            plot_closing=os.path.relpath(closing_path, settings.BASE_DIR),
            plot_cmp=os.path.relpath(cmp_path, settings.BASE_DIR),
            metrics={"window": window, "data_points": len(df)},
        )
        return prediction

    except Exception as e:
        # Cleanup any files that were written before failure
        for path in (closing_path, cmp_path):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
        raise e
