#!/bin/bash

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

if [ -n "$1" ] && [ "$1" -gt "-1" ]
then
    bport=$1
else
    bport=5000
fi

uvicorn main:app --port $bport --host=0.0.0.0 --reload
