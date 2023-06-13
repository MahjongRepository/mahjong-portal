#!/bin/bash

TYPE=$1
DIR="/root/portal/backups"
BACKUP_FILE="/tmp/portal.sql"

mkdir -p $DIR/$TYPE/

# perform rotations
if [[ "$TYPE" == "hourly" ]]; then
    FILENAME=$DIR/$TYPE/`date +%Y-%m-%d-%H-%M-%S.sql.gz`

    # keep latest 12 hourly backups only
    cd $DIR/$TYPE/ && ls -t1 | tail -n +13 | xargs rm -r
else
    FILENAME=$DIR/$TYPE/`date +%Y-%m-%d.sql.gz`

    # keep latest 3 backups only
    cd $DIR/$TYPE/ && ls -t1 | tail -n +3 | xargs rm -r
fi

zip -r $FILENAME $BACKUP_FILE
rm $BACKUP_FILE
