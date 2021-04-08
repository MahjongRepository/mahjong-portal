FROM python:3.9.4-slim

ENV PYTHONUNBUFFERED=1

RUN useradd -ms /bin/bash docker-user

RUN python3 -m pip install pip==21.0.1

RUN apt-get update && apt-get install --allow-remove-essential -y \
    gettext \
    libpq-dev \
    python-dev \
    gcc

COPY ./server/requirements/base.txt /requirements.txt
COPY ./server/requirements/base.txt /base.txt
COPY ./server/requirements/dev.txt /dev.txt

# let's install additional dev package only if there is no production build
ARG mode
RUN echo "Mode=$mode"
RUN if [ "$mode" != "production" ] ; then cat /base.txt /dev.txt > /requirements.txt ; fi

RUN python3 -m pip install -r /requirements.txt --no-cache-dir

COPY ./docker/django/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r//' /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY ./docker/django/cron_entrypoint.sh /cron_entrypoint.sh
RUN sed -i 's/\r//' /cron_entrypoint.sh
RUN chmod +x /cron_entrypoint.sh

ADD ./docker/django/crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab

# clean up apt packages
RUN apt-get remove -y libpq-dev gcc python-dev && rm -rf /var/lib/apt/lists/*

COPY ./server/ /app/
WORKDIR /app/

RUN rm /requirements.txt
RUN rm /base.txt
RUN rm /dev.txt
RUN rm -r /app/requirements/

USER docker-user

ENTRYPOINT ["/entrypoint.sh"]
