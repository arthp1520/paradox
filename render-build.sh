#!/usr/bin/env bash
# run migrations and collect static files
python manage.py migrate --noinput
python manage.py collectstatic --noinput
