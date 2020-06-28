COMPOSE_FILE=$(or $(COMPOSE_FILE_VAR), local.yml)

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

test:
	docker-compose -f local.yml run -u `id -u` --rm web python manage.py test --noinput

lint:
	pre-commit run -u `id -u` --all-files

initial_data:
	docker-compose -f local.yml run -u `id -u` --rm web python manage.py flush --noinput
	docker-compose -f local.yml run -u `id -u` --rm web python manage.py migrate --noinput
	docker-compose -f local.yml run -u `id -u` --rm web python manage.py initial_data
