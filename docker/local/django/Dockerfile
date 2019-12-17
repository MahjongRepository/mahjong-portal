FROM python:3.7.3

ENV PYTHONUNBUFFERED 1

# Requirements are installed here to ensure they will be cached.
COPY ./server/requirements /requirements
RUN pip install --upgrade pip
RUN pip install -r /requirements/local.txt

COPY ./docker/local/django/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r//' /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY ./docker/local/django/start.sh /start.sh
RUN sed -i 's/\r//' /start.sh
RUN chmod +x /start.sh

RUN apt-get update
RUN apt-get install gettext

COPY . /app
WORKDIR /app/server

ENTRYPOINT ["/entrypoint.sh"]
