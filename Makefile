build:
	docker-compose build

up:
	docker-compose up -d

stop:
	docker-compose stop

logs:
	docker-compose logs -f web_portal

restore_db:
	${MAKE} up
	sleep 5
	docker-compose exec db_portal psql -U postgres mahjong_portal -c "REVOKE CONNECT ON DATABASE mahjong_portal FROM public; SELECT pid, pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();"
	docker-compose exec db_portal dropdb -U postgres mahjong_portal
	docker-compose exec db_portal createdb -U postgres mahjong_portal
	docker-compose exec db_portal sh -c "psql -U postgres mahjong_portal < /files/latest.sql"
	docker-compose exec web_portal python manage.py migrate --noinput
	${MAKE} stop
	${MAKE} up