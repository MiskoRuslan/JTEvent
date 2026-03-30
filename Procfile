web: gunicorn event_management.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120 --log-file -
worker: celery -A event_management worker --loglevel=info --concurrency=2
beat: celery -A event_management beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
