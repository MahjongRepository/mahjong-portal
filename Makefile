COMPOSE_FILE=$(or $(COMPOSE_FILE_VAR), local.yml)

up:
	docker-compose -f $(COMPOSE_FILE) up -d

stop:
	docker-compose -f $(COMPOSE_FILE) stop

console:
	${MAKE} up
	docker-compose -f $(COMPOSE_FILE) run --rm web bash

build:
	docker-compose -f $(COMPOSE_FILE) build

initial_data:
	docker-compose -f local.yml run --rm web python manage.py migrate --noinput
	docker-compose -f local.yml run --rm web python manage.py initial_data

permissions:
	sudo chown -R $$USER:$$USER .

django_logs:
	docker-compose -f $(COMPOSE_FILE) logs -f web