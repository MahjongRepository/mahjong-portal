FROM python:3.9.13-alpine

ENV PYTHONUNBUFFERED=1

RUN python3 -m pip install pip==22.1.2

COPY ./server/requirements/base.txt /requirements.txt
COPY ./server/requirements/base.txt /base.txt
COPY ./server/requirements/dev.txt /dev.txt

# let's install additional dev package only if there is no production build
ARG mode
RUN echo "Mode=$mode"
RUN if [ "$mode" != "production" ] ; then cat /base.txt /dev.txt > /requirements.txt ; fi

RUN apk update && apk add libpq gettext-dev

RUN \
 apk add --no-cache --virtual .build-deps postgresql-dev gcc musl-dev && \
 python3 -m pip install -r /requirements.txt --no-cache-dir && \
 apk --purge del .build-deps

COPY ./docker/django/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r//' /entrypoint.sh
RUN chmod +x /entrypoint.sh

ADD ./docker/django/crontab /etc/crontabs/root

RUN addgroup -S docker && adduser -S docker-user -G docker

COPY ./server/ /app/
WORKDIR /app/

RUN rm /requirements.txt
RUN rm /base.txt
RUN rm /dev.txt
RUN rm -r /app/requirements/

ENTRYPOINT ["/entrypoint.sh"]

RUN mkdir -p /django_cache
RUN chown docker-user /django_cache

USER docker-user
