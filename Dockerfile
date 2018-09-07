FROM python:3.6

RUN pip3 install --upgrade pip

ENV SRC_PROJECT_PATH /code
RUN mkdir -p $SRC_PROJECT_PATH

WORKDIR $SRC_PROJECT_PATH

COPY ./server/requirements.pip $SRC_PROJECT_PATH/

RUN pip3 install -r requirements.pip

COPY ./server $SRC_PROJECT_PATH

CMD ["gunicorn", "mahjong_portal.wsgi:application"]

EXPOSE 8081

