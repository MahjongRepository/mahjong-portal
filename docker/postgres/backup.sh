#!/bin/bash

DIR="/backups/"

KEEP_DAILY=7
KEEP_WEEKLY=5
KEEP_MONTHLY=12

PGPASSWORD=$POSTGRES_PASSWORD --rm db pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER $POSTGRES_DB > dump_`date +%d-%m-%Y"_"%H_%M_%S`.sql

exit 1

function rotate {
    rotation=$1
    fdate=`date +%Y-%m-%d -d $date`
    file=$DIR/daily/*$fdate*.gz
    mkdir -p $DIR/$rotation/ || abort
    if [ -f $file ]; then
        cp $file $DIR/$rotation/ || abort
    else
        echo
    fi
}

function prune {
    dir=$DIR/$1
    keep=$2
    ls $dir | sort -rn | awk " NR > $keep" | while read f; do rm $dir/$f; done
}

function abort {
    echo "aborting..."
    exit 1
}

mkdir -p $DIR/daily || abort
mkdir -p $DIR/weekly || abort
mkdir -p $DIR/monthly || abort
mkdir -p $DIR/yearly || abort

date=`date +%Y-%m-%d` || abort
day=`date -d $date +%d` || abort
weekday=`date -d $date +%w` || abort
month=`date -d $date +%m` || abort

# Do the daily backup
/usr/bin/pg_dump $DB $DUMP_ARGS | gzip > $DIR/daily/${DB}_$date.sql.gz
test ${PIPESTATUS[0]} -eq 0 || abort

# Perform rotations
if [[ "$weekday" == "0" ]]; then
    rotate weekly
fi
if [[ "$day" == "01" ]]; then
    rotate monthly
fi
if [[ "$month/$day" == "01/01" ]]; then
    rotate yearly
fi

prune daily $KEEP_DAILY
prune weekly $KEEP_WEEKLY
prune monthly $KEEP_MONTHLY