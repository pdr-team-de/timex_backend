#!/usr/bin/env bash
set -o errexit

echo "Installing Python packages..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if [ "$RENDER" = "true" ]; then
    echo "Running on Render.com..."
    echo "Waiting for database..."
    sleep 10  # Give the database time to start
    
    echo "Running migrations..."
    python manage.py migrate --noinput
    
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
    
    echo "Creating initial admin user..."
    python manage.py create_initial_admin
fi