FROM python:3.9.1-slim

ENV PYTHONUNBUFFERED 1

RUN useradd -ms /bin/bash docker-user

RUN apt-get update && apt-get install --allow-remove-essential -y \
    gettext \
    libpq-dev \
    python-dev \
    gcc

# Requirements are installed here to ensure they will be cached.
COPY ./server/requirements /requirements
RUN pip install --upgrade pip
RUN pip install -r /requirements/local.txt

COPY ./docker/local/django/entrypoint.sh /entrypoint.sh
COPY ./docker/local/django/cron_entrypoint.sh /cron_entrypoint.sh
COPY ./docker/local/django/backup.sh /backup.sh

ADD ./docker/production/django/crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab

# clean up apt packages
RUN apt-get remove -y libpq-dev gcc python-dev && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app/server

USER docker-user

ENTRYPOINT ["/entrypoint.sh"]
