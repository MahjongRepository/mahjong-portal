COMPOSE_FILE=$(or $(COMPOSE_FILE_VAR), local.yml)
GREEN = $(shell echo -e '\033[1;32m')
NC = $(shell echo -e '\033[0m') # No Color

console:
	${MAKE} up
	docker-compose -f $(COMPOSE_FILE) run --rm web bash

build:
	docker-compose -f $(COMPOSE_FILE) build --no-cache

initial_data:
#	docker-compose -f local.yml run --rm web python manage.py migrate --noinput
	docker-compose -f local.yml run --rm web python manage.py initial_data

up:
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "${GREEN}Project live at http://127.0.0.1:8060/${NC}"

stop:
	docker-compose -f $(COMPOSE_FILE) stop

permissions:
	sudo chown -R $$USER:$$USER .

django_logs:
	docker-compose -f $(COMPOSE_FILE) logs -f web