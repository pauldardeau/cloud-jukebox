#!/bin/sh
if [ $# -eq 0 ] ; then
   echo "error: missing artist name"
   echo 'example: ./play-artist.sh "Van Halen"'
   exit 1
fi
python3 jukebox_main.py --storage s3 --artist="$1" play
