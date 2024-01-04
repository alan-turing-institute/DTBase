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
    debug=false
    if [ -z "$FLASK_DEBUG" ]; then
        export FLASK_DEBUG=false
    fi
else
    debug=true
    if [ -z "$FLASK_DEBUG" ]; then
        export FLASK_DEBUG=true
    fi
fi

npm install
if [ "$debug" == "false" ]; then
  npx webpack --mode=production
  flask run --host=0.0.0.0 --port $bport
else
  # This runs webpack and the flask app concurrently.
  # This only matters when in development/debug mode, in which case we run webpack with
  # --watch, to have it retranspile and bundle every time a source file is changed.
  npx concurrently --kill-others -n webpack,flask "npx webpack --mode=development --watch" "flask run --host=0.0.0.0 --port $bport"
fi
