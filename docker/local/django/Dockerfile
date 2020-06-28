FROM python:3.8.3-slim

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
RUN sed -i 's/\r//' /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY ./docker/local/django/start.sh /start.sh
RUN sed -i 's/\r//' /start.sh
RUN chmod +x /start.sh

# clean up apt packages
RUN apt-get remove -y libpq-dev gcc python-dev \
 && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app/server

USER docker-user

ENTRYPOINT ["/entrypoint.sh"]
