#!/bin/bash
set -e

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Starting gunicorn..."
exec gunicorn helpdesk.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
