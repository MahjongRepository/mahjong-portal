#!/usr/bin/env bash

set -e
/srv/scripts/wait_for_db.sh
./manage.py migrate
exec "$@"
