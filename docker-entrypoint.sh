#!/bin/sh
set -eu

flask --app wsgi db upgrade
exec gunicorn --bind 0.0.0.0:5050 --workers 2 --access-logfile - wsgi:app
