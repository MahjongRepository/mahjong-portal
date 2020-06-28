FROM python:3.8.3-slim

ENV PYTHONUNBUFFERED 1

# Requirements are installed here to ensure they will be cached.
COPY ./server/requirements /requirements
RUN pip install --upgrade pip
RUN pip install -r /requirements/production.txt

RUN useradd -ms /bin/bash docker-user

COPY ./docker/production/django/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r//' /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY ./docker/production/django/start.sh /start.sh
RUN sed -i 's/\r//' /start.sh
RUN chmod +x /start.sh

COPY ./docker/production/django/cron_entrypoint.sh /cron_entrypoint.sh
RUN sed -i 's/\r//' /cron_entrypoint.sh
RUN chmod +x /cron_entrypoint.sh

RUN apt-get update
RUN apt-get -y install cron
ADD ./docker/production/django/crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab

COPY . /app
WORKDIR /app/server

USER docker-user

ENTRYPOINT ["/entrypoint.sh"]
