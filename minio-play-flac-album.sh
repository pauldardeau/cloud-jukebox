#!/bin/sh
if [ $# -eq 0 ] ; then
   echo "error: missing artist name and album name"
   echo 'example: ./minio-play-flac-album.sh "ZZ Top" "Eliminator"'
   exit 1
fi
python3 jukebox_main.py --storage minio --artist "$1" --album "$2" --format "flac" play
