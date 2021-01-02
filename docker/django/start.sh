#!/bin/sh

set -o errexit
set -o nounset

python /app/server/manage.py migrate
python /app/server/manage.py collectstatic --noinput --clear --verbosity 0
python /app/server/manage.py rebuild_index --noinput

/usr/local/bin/gunicorn mahjong_portal.wsgi \
--bind=0.0.0.0:${GUNICORN_PORT} \
--workers=${GUNICORN_WORKERS} \
--log-level=info
--chdir=/app/server
