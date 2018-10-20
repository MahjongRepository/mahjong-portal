#!/usr/bin/env bash

set -e
/srv/scripts/localize.py < mahjong_portal/settings/local.example.py > mahjong_portal/settings/local.py
/srv/scripts/wait_for_db.py
./manage.py migrate
exec "$@"
