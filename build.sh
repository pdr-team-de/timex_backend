#!/usr/bin/env bash
set -o errexit

echo "Installing Python packages..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if [ "$RENDER" = "true" ]; then
    echo "Running on Render.com..."
    echo "Waiting for database..."
    # Increase sleep time to ensure database is ready
    sleep 20
    
    echo "Running migrations..."
    python manage.py migrate --noinput || {
        echo "Migration failed. Retrying in 10 seconds..."
        sleep 10
        python manage.py migrate --noinput
    }
    
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
else
    echo "Running locally..."
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput
fi