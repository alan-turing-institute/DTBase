#!/bin/bash

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

export FLASK_APP=frontend_app.py

if [ -n "$1" ] && [ "$1" -gt "-1" ]
then
    bport=$1
else
    bport=8000
fi

if [ -z "$DT_CONFIG_MODE" ] || [ "$DT_CONFIG_MODE" == "Production" ]; then
    webpack_mode="production"
    tsc_options=""
    if [ -z "$FLASK_DEBUG" ]; then
        export FLASK_DEBUG=false
    fi
else
    webpack_mode="development"
    tsc_options=" --watch"
    if [ -z "$FLASK_DEBUG" ]; then
        export FLASK_DEBUG=true
    fi
fi

npm install
# This runs tsc to transpile typescript into javascript and the flask app concurrently.
# This only matters when in development/debug mode, in which case we run tsc with --watch, to have it
# retranspile every time a source file is changed.
npx concurrently --kill-others -n tsc,flask "npx tsc ${tsc_options}" "flask run --host=0.0.0.0 --port $bport"
