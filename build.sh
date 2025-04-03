#!/usr/bin/env bash
set -o errexit

# Python packages installation
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input