FROM python:3.7.3

ENV PYTHONUNBUFFERED 1

# Requirements are installed here to ensure they will be cached.
COPY ./server/requirements /requirements
RUN pip install --upgrade pip
RUN pip install -r /requirements/production.txt

COPY ./docker/production/django/entrypoint /entrypoint
RUN sed -i 's/\r//' /entrypoint
RUN chmod +x /entrypoint

COPY ./docker/production/django/start /start
RUN sed -i 's/\r//' /start
RUN chmod +x /start

RUN apt-get update
RUN apt-get -y install cron
ADD ./docker/production/django/crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab

COPY . /app
WORKDIR /app/server

ENTRYPOINT ["/entrypoint.sh"]