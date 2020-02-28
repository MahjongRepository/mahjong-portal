COMPOSE_FILE=$(or $(COMPOSE_FILE_VAR), local.yml)

up:
	docker-compose -f $(COMPOSE_FILE) up

stop:
	docker-compose -f $(COMPOSE_FILE) stop

logs:
	docker-compose -f $(COMPOSE_FILE) logs -f

web:
	${MAKE} up
	docker-compose -f $(COMPOSE_FILE) run --rm web bash

build:
	docker-compose -f $(COMPOSE_FILE) build

test:
	${MAKE} up
	docker-compose -f local.yml run --rm web python manage.py test --noinput

lint:
	${MAKE} up
	docker-compose -f local.yml run --rm web flake8 --config=../.flake8

initial_data:
	docker-compose -f local.yml run --rm web python manage.py flush --noinput
	docker-compose -f local.yml run --rm web python manage.py migrate --noinput
	docker-compose -f local.yml run --rm web python manage.py initial_data

permissions:
	sudo chown -R $$USER:$$USER .
