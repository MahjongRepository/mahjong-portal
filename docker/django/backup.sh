#!/bin/bash

TYPE=$1
DIR="/backups"

mkdir -p $DIR/$TYPE/

# perform rotations
if [[ "$TYPE" == "hourly" ]]; then
    FILENAME=$DIR/hourly/`date +%Y-%m-%d-%H-%M-%S.sql.gz`

    # keep latest 12 hourly backups only
    cd $DIR/hourly/ && ls -t1 | tail -n +13 | xargs rm -r
else
    FILENAME=$DIR/$TYPE/`date +%Y-%m-%d.sql.gz`
    # keep latest 4 backups only
    cd $DIR/$TYPE/ && ls -t1 | tail -n +5 | xargs rm -r
fi

PGPASSWORD=$POSTGRES_PASSWORD pg_dump -h db -U $POSTGRES_USER $POSTGRES_DB | gzip > $FILENAME
echo "$FILENAME created";
