up:
	docker compose up

down:
	docker compose stop

logs:
	docker compose logs -f

shell:
	docker compose run --user=root --rm web sh

build-docker:
	docker compose build

initial-data:
	docker compose run -u `id -u` --rm web python manage.py flush --noinput
	docker compose run -u `id -u` --rm web python manage.py migrate --noinput
	docker compose run -u `id -u` --rm web python manage.py initial_data

test:
	docker compose run -u `id -u` --rm web python manage.py test --noinput

# usage example "make db-restore dump=~/Downloads/dump.sql"
db-restore:
	docker compose up --detach db

	docker compose run --rm db sh -c \
  	'PGPASSWORD=$$POSTGRES_PASSWORD dropdb -U $$POSTGRES_USER -h $$POSTGRES_HOST $$POSTGRES_DB --if-exists' \
  	--env-file .envs/.local

	docker compose run --rm db sh -c \
	'PGPASSWORD=$$POSTGRES_PASSWORD createdb -U $$POSTGRES_USER -h $$POSTGRES_HOST $$POSTGRES_DB' \
	--env-file .envs/.local

	docker compose run \
	-v $(dump):/tmp/dump.sql \
	--rm db sh -c 'PGPASSWORD=$$POSTGRES_PASSWORD psql -U $$POSTGRES_USER -h $$POSTGRES_HOST $$POSTGRES_DB < /tmp/dump.sql' \
	--env-file .envs/.local

release-docker-image:
	docker buildx build --push \
		--build-arg mode=production \
		--tag ghcr.io/mahjongrepository/mahjong-portal:latest \
		--tag ghcr.io/mahjongrepository/mahjong-portal:$(shell git show-ref refs/heads/master --hash=7) \
		--file ./docker/django/Dockerfile .

#### Code formatters and linters ####

lint: lint-isort lint-python-code-style lint-flake8
format: format-isort format-python-code

lint-python-code-style:
	docker compose run -u `id -u` --rm web black --check .

lint-isort:
	docker compose run -u `id -u` --rm web isort --check-only .

lint-flake8:
	docker compose run -u `id -u` --rm web flake8 .

format-python-code:
	docker compose run -u `id -u` --rm web black .

format-isort:
	docker compose run -u `id -u` --rm web isort .

