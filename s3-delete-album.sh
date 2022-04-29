#!/bin/sh
if [ $# -eq 0 ]; then
   echo "error: missing album identifier"
   exit 1
fi
python3 jukebox_main.py --storage s3 --album "$1" delete-album
