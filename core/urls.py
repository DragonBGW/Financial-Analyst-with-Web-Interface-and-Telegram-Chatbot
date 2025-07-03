from django.urls import path, include
from .views_frontend import register, login, logout, dashboard
from .views import RegisterView, PredictView, PredictionListView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # API endpoints
    path("register/",      RegisterView.as_view()),         # /api/v1/register/  (already namespaced higher)
    path("token/",         TokenObtainPairView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view()),
    path("predict/",       PredictView.as_view()),
    path("predictions/",   PredictionListView.as_view()),

    # Front‑end
    path("frontend/register/", register, name="register"),
    path("frontend/login/",    login,    name="login"),
    path("frontend/logout/",   logout,   name="logout"),
    path("frontend/dashboard/", dashboard, name="dashboard"),  
]


# core/utils.py
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
from django.conf import settings
from .models import Prediction
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import io, os, base64, uuid, pandas as pd

MODEL = load_model(os.getenv("MODEL_PATH", "stock_prediction_model.keras"))

def run_prediction(user, ticker: str) -> Prediction:
    df = yf.download(ticker, period="10y", interval="1d")
    if df.empty:
        raise ValueError(f"Ticker {ticker} returned no data")

    close_prices = df["Close"].values.reshape(-1, 1)
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(close_prices)

    X_test = scaled[-60:].reshape(1, 60, 1)   # assuming model expects 60‑day window
    pred_scaled = MODEL.predict(X_test)[0][0]
    pred_price  = scaler.inverse_transform([[pred_scaled]])[0][0]

    # simple metrics placeholder
    mse  = float(np.mean((scaled[-1] - pred_scaled) ** 2))
    rmse = float(np.sqrt(mse))
    r2   = float(1 - mse / np.var(scaled[-60:]))

    # Plot 1: closing history
    plt.figure()
    df["Close"].plot(title=f"{ticker} Closing Price")
    closing_fname = f"static/plots/{uuid.uuid4()}_close.png"
    plt.savefig(closing_fname)
    plt.close()

    # Plot 2: compare last 60 vs prediction
    plt.figure()
    last_60 = scaler.inverse_transform(scaled[-60:])
    plt.plot(pd.date_range(end=df.index[-1], periods=60), last_60, label="Actual")
    plt.scatter([df.index[-1] + pd.Timedelta(days=1)], [pred_price], label="Predicted")
    plt.legend()
    cmp_fname = f"static/plots/{uuid.uuid4()}_cmp.png"
    plt.savefig(cmp_fname)
    plt.close()

    return Prediction.objects.create(
        user=user,
        ticker=ticker.upper(),
        next_price=pred_price,
        mse=mse,
        rmse=rmse,
        r2=r2,
        plot_closing=closing_fname,
        plot_cmp=cmp_fname,
        metrics={"window": 60}
    )

