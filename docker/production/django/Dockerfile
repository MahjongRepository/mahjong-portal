FROM python:3.7.3

ENV PYTHONUNBUFFERED 1

# Requirements are installed here to ensure they will be cached.
COPY ./server/requirements /requirements
RUN pip install --upgrade pip
RUN pip install -r /requirements/production.txt

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

# we need to save variables in file special for cron
RUN /bin/bash -c declare -p | grep -Ev 'BASHOPTS|BASH_VERSINFO|EUID|PPID|SHELLOPTS|UID' > /cron.env

COPY . /app
WORKDIR /app/server

ENTRYPOINT ["/entrypoint.sh"]