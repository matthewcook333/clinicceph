#!/bin/bash

FILE_PATH=$1
SERVER_NAME=$2
OUT_FOLDER=$3

if [ ! -d "$OUT_FOLDER" ]; then
    mkdir "$OUT_FOLDER"
fi

# Exits with status of this rsync, so missing file errors
rsync -caz -e "ssh -oBatchMode=yes" "$SERVER_NAME:$FILE_PATH" "$OUT_FOLDER"
