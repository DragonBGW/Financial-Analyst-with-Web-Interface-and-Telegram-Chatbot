#!/usr/bin/env sh
set -e

echo "🔧 Running Django migrations..."
python manage.py migrate --noinput

echo "🎯 Collecting static files..."
python manage.py collectstatic --noinput

echo "🚀 Starting Gunicorn..."
exec gunicorn stock_prediction_main.wsgi:application \
     --bind 0.0.0.0:$PORT --timeout 120
