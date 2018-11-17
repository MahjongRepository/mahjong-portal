#!/bin/sh

set -o errexit
set -o nounset

psql "${POSTGRES_DB}" -c "REVOKE CONNECT ON DATABASE \"${POSTGRES_DB}\" FROM public; SELECT pid, pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();"

message_info "Dropping the database..."
dropdb "${POSTGRES_DB}"

message_info "Creating a new database..."
createdb --owner="${POSTGRES_USER}"

message_info "Applying the backup to the new database..."
pg_restore --no-owner --no-privileges --no-tablespaces --schema public -Fc -d ${POSTGRES_DB} /docker-entrypoint-initdb.d/latest.sql
