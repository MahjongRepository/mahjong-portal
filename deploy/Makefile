update:
	docker compose pull
	docker compose down
	docker compose run -u `id -u` --rm web python manage.py collectstatic --no-input --clear
	docker compose run -u `id -u` --rm web python manage.py migrate
	docker compose up -d

down:
	docker compose down

shell:
	docker compose run -u `id -u` --rm web sh

db-backup:
	docker compose up --detach db
	docker compose run \
		-v /tmp/:/tmp/ \
		--user=root \
		--rm db sh -c \
  		'PGPASSWORD=$$POSTGRES_PASSWORD pg_dump -h db -U $$POSTGRES_USER $$POSTGRES_DB > /tmp/portal.sql'
	bash ./backup.sh $(backup_type)
