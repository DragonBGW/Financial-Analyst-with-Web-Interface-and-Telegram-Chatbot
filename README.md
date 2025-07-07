# 📈 Financial Analyst with Web Interface and Telegram Chatbot

A full-stack Django web app that predicts the **next-day closing price of stocks** using a trained deep learning model (Keras), integrates **Stripe** for paid subscriptions, and includes a **Telegram bot** interface for prediction via chat.
---
## 🚀 Features

- 🧠 LSTM-based next-day stock price prediction
- 📉 Dynamic charts with Matplotlib (Docker-compatible using `Agg` backend)
- 🧾 Stripe integration for paid subscriptions (Pro users)
- 🤖 Telegram bot (`/predict <TICKER>`) support via `python-telegram-bot`
- 🐳 Dockerized for production & local development

---
## 📦 Project Structure
stockinsightML/
├── core/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── signals.py
│   ├── utils.py
│   ├── views_payment.py
│   ├── views_billing.py
│   ├── views_frontend.py
│   ├── management/
│   │   └── commands/
│   │       └── telegrambot.py
│   ├── templates/
│   │   └── billing/
│   │       ├── subscribe.html
│   │       └── success.html
│   └── ...
├── stock_prediction_main/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── .env
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── db.sqlite3
└── README.md

📦yaml
---
## ⚙️ Environment Variables (`.env`)
Create a `.env` file in your root:
dotenv
DEBUG=True
SECRET_KEY=your_django_secret_key

# Stripe keys
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PRICE_ID=price_abc123   # create this in Stripe dashboard
BOT_TOKEN=your_telegram_bot_token

# ML model path
MODEL_PATH=stock_prediction_model.keras

🐳 Docker Setup
1.Build and run both the web server and the Telegram bot via Docker:
docker compose up --build

2.If you want to rebuild after a change:
docker compose down
docker compose up --build
After starting the Web App in your localHost machine, you will see something like this 
<img width="487" alt="image" src="https://github.com/user-attachments/assets/a49d187e-6379-4c1f-85c6-51f37dd0f036" />

If you log in with your credentials (if you haven't before you can register from the website, or you can create a superuser in your django app when running local), you will see like the following 
<img width="487" alt="image" src="https://github.com/user-attachments/assets/8082a74d-5b63-4237-be88-8ef43e37ebbb" />

3. Run Migrations
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

📡 Telegram Bot
Start the bot via Docker:
docker compose up bot

Meanwhile, you can check Healthz status with command lines described as following,
<img width="476" alt="image" src="https://github.com/user-attachments/assets/fa10ff00-8495-4d92-99cb-6d8d708552f5" />

Also you can see the same thing in website, 
<img width="491" alt="image" src="https://github.com/user-attachments/assets/af0a024f-bf8c-48ab-838d-3a42d9ba74cc" />

Or locally:
python manage.py telegrambot

Try:
/start

🧪 Local Development (non-Docker)
Install dependencies:
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

Run the app:
python manage.py runserver

🌐 Web UI (Django + Tailwind CSS)
1. Built using Django views and templates.
2.Styled with Tailwind CSS (no Bootstrap).
3. Users can:
a.Register/login securely.
b. Input a stock ticker (e.g., AAPL) to get predictions.
c. View price plots and ML metrics (RMSE, R²).
d.Upgrade to Pro via Stripe subscription.
4. Pro-only features gated by is_pro flag in user profile.


💳 Stripe Integration
1. Visit /subscribe/ to see the pricing page.
2. On success, user is marked as is_pro = True (in UserProfile).
3. Cancel/success redirects handled without webhooks (basic plan).

For real-time updates, configure /webhooks/stripe/ and add webhook secret in .env.

🧠 Model Info
Model file: stock_prediction_model.keras
Prediction is done via core/utils.py
Uses 60-day sliding window of closing prices and MinMax scaling

🖼 Plot Storage
Prediction and historical plots are saved in static/plots/
Paths are stored in the database (relative to BASE_DIR)

📄 Example .gitignore
venv/
*.pyc
__pycache__/
*.sqlite3
*.keras
.env
static/plots/












