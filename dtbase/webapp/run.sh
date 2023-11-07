#!/bin/bash

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

export FLASK_APP=frontend_app.py
export FLASK_ENV=development

if [ -n "$1" ] && [ "$1" -gt "-1" ]
then
    bport=$1
else
    bport=8000
fi

npm install
flask run --host=0.0.0.0 --port $bport
