#!/bin/bash

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

export FLASK_APP=dtbase_app.py

if test -f "../../.secrets/dtenv_localdb.sh"; then
    source ../../.secrets/dtenv_localdb.sh
fi

# start the postgres docker container, if it isn't already running.
dtbase_start_postgres_docker

if [ -n "$1" ] && [ "$1" -gt "-1" ]
then
    bport=$1
else
    bport=5000
fi

uvicorn dtbase_app:app --port $bport --reload
