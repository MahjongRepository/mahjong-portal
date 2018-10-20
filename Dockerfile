FROM python:3.6

ENV SRC_PROJECT_PATH /srv/mahjong-portal/

RUN mkdir -p $SRC_PROJECT_PATH

WORKDIR $SRC_PROJECT_PATH

COPY server/requirements.pip /tmp/

RUN pip install -r /tmp/requirements.pip \
    && rm /tmp/requirements.pip

COPY scripts/ /srv/scripts/

COPY server $SRC_PROJECT_PATH

ENTRYPOINT ["/srv/scripts/docker-entrypoint.sh"]

CMD ["gunicorn", "mahjong_portal.wsgi:application"]
