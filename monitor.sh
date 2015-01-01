#!/bin/bash

FILE_PATH=$1
SERVERS_FILE=$2
OUT_FOLDER=$3
KEY_FILE=$4
USER=$5

if [ ! -d "$OUT_FOLDER" ]; then
    mkdir "$OUT_FOLDER"
fi

while read line; do
    rsync -i "$KEY_FILE" -a "$5@$line:$FILE_PATH" "$OUT_FOLDER"
done < $SERVERS_FILE
