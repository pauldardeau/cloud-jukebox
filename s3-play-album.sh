#!/bin/sh
if [ $# -eq 0 ] ; then
   echo "error: missing artist name and album name"
   echo 'example: ./s3-play-album.sh "ZZ Top" "Eliminator"'
   exit 1
fi
python3 jukebox_main.py --storage s3 --artist="$1" --album="$2" play-album
