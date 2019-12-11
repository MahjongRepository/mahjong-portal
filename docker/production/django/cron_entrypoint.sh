#!/bin/sh

set -o errexit
set -o nounset

export DATABASE_URL="postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
echo $DATABASE_URL;
echo "test";

exec "$@"