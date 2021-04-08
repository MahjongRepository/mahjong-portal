COMPOSE_FILE=$(or $(COMPOSE_FILE_VAR), docker-compose.yml)

up:
	docker-compose -f $(COMPOSE_FILE) up

up_daemon:
	docker-compose -f $(COMPOSE_FILE) up -d

down:
	docker-compose -f $(COMPOSE_FILE) stop

logs:
	docker-compose -f $(COMPOSE_FILE) logs -f

shell:
	docker-compose -f $(COMPOSE_FILE) run -u `id -u` --rm web bash

build_docker:
	docker-compose -f $(COMPOSE_FILE) build

initial_data:
	docker-compose -f local.yml run -u `id -u` --rm web python manage.py flush --noinput
	docker-compose -f local.yml run -u `id -u` --rm web python manage.py migrate --noinput
	docker-compose -f local.yml run -u `id -u` --rm web python manage.py initial_data

test:
	docker-compose -f local.yml run -u `id -u` --rm web python manage.py test --noinput

# usage example "make db_restore dump=~/Downloads/dump.sql"
db_restore:
	docker-compose -f local.yml up --detach db

	docker-compose -f local.yml run --rm db bash -c \
  	'PGPASSWORD=$$POSTGRES_PASSWORD dropdb -U $$POSTGRES_USER -h $$POSTGRES_HOST $$POSTGRES_DB --if-exists' \
  	--env-file .envs/.local/.postgres

	docker-compose -f local.yml run --rm db bash -c \
	'PGPASSWORD=$$POSTGRES_PASSWORD createdb -U $$POSTGRES_USER -h $$POSTGRES_HOST $$POSTGRES_DB' \
	--env-file .envs/.local/.postgres

	docker-compose -f local.yml run \
	-v $(dump):/tmp/dump.sql \
	--rm db bash -c 'PGPASSWORD=$$POSTGRES_PASSWORD psql -U $$POSTGRES_USER -h $$POSTGRES_HOST $$POSTGRES_DB < /tmp/dump.sql' \
	--env-file .envs/.local/.postgres

#### Code formatters and linters ####

lint: lint-isort lint-python-code-style lint-flake8
format: format-isort format-python-code

lint-python-code-style:
	docker-compose -f $(COMPOSE_FILE) run -u `id -u` --rm web black --check .

lint-isort:
	docker-compose -f $(COMPOSE_FILE) run -u `id -u` --rm web isort -rc --check-only .

lint-flake8:
	docker-compose -f $(COMPOSE_FILE) run -u `id -u` --rm web flake8 .

format-python-code:
	docker-compose -f $(COMPOSE_FILE) run -u `id -u` --rm web black .

format-isort:
	docker-compose -f $(COMPOSE_FILE) run -u `id -u` --rm web isort -rc .

