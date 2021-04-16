COMPOSE_FILE=$(or $(COMPOSE_FILE_VAR), docker-compose.yml)

up:
	docker-compose -f $(COMPOSE_FILE) up

up-daemon:
	docker-compose -f $(COMPOSE_FILE) up -d

down:
	docker-compose -f $(COMPOSE_FILE) stop

run-production-update: down run-migrations-collectstatic-search-index up-daemon

run-migrations-collectstatic-search-index:
	docker-compose -f $(COMPOSE_FILE) pull
	docker-compose -f $(COMPOSE_FILE) run -u `id -u` --rm web python manage.py migrate
	docker-compose -f $(COMPOSE_FILE) run -u `id -u` --rm web python manage.py collectstatic --noinput --clear

logs:
	docker-compose -f $(COMPOSE_FILE) logs -f

shell:
	docker-compose -f $(COMPOSE_FILE) run --user=root --rm web sh

build-docker:
	docker-compose -f $(COMPOSE_FILE) build

initial-data:
	docker-compose -f $(COMPOSE_FILE) run -u `id -u` --rm web python manage.py flush --noinput
	docker-compose -f $(COMPOSE_FILE) run -u `id -u` --rm web python manage.py migrate --noinput
	docker-compose -f $(COMPOSE_FILE) run -u `id -u` --rm web python manage.py initial-data

test:
	docker-compose -f $(COMPOSE_FILE) run -u `id -u` --rm web python manage.py test --noinput

# usage example "make db-restore dump=~/Downloads/dump.sql"
db-restore:
	docker-compose -f $(COMPOSE_FILE) up --detach db

	docker-compose -f $(COMPOSE_FILE) run --rm db sh -c \
  	'PGPASSWORD=$$POSTGRES_PASSWORD dropdb -U $$POSTGRES_USER -h $$POSTGRES_HOST $$POSTGRES_DB --if-exists' \
  	--env-file .envs/.local

	docker-compose -f $(COMPOSE_FILE) run --rm db sh -c \
	'PGPASSWORD=$$POSTGRES_PASSWORD createdb -U $$POSTGRES_USER -h $$POSTGRES_HOST $$POSTGRES_DB' \
	--env-file .envs/.local

	docker-compose -f $(COMPOSE_FILE) run \
	-v $(dump):/tmp/dump.sql \
	--rm db sh -c 'PGPASSWORD=$$POSTGRES_PASSWORD psql -U $$POSTGRES_USER -h $$POSTGRES_HOST $$POSTGRES_DB < /tmp/dump.sql' \
	--env-file .envs/.local

release-docker-image:
	docker buildx build --push \
		--build-arg mode=production \
		--tag ghcr.io/mahjongrepository/mahjong-portal:latest \
		--tag ghcr.io/mahjongrepository/mahjong-portal:$(shell git show-ref refs/heads/master --hash) \
		--file ./docker/django/Dockerfile .

#### Code formatters and linters ####

lint: lint-isort lint-python-code-style lint-flake8
format: format-isort format-python-code

lint-python-code-style:
	docker-compose -f $(COMPOSE_FILE) run -u `id -u` --rm web black --check .

lint-isort:
	docker-compose -f $(COMPOSE_FILE) run -u `id -u` --rm web isort --check-only .

lint-flake8:
	docker-compose -f $(COMPOSE_FILE) run -u `id -u` --rm web flake8 .

format-python-code:
	docker-compose -f $(COMPOSE_FILE) run -u `id -u` --rm web black .

format-isort:
	docker-compose -f $(COMPOSE_FILE) run -u `id -u` --rm web isort .

