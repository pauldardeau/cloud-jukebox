#!/bin/sh
if [ $# -eq 0 ] ; then
   echo "error: missing artist name"
   echo 'example: ./play-artist.sh "Van Halen"'
   exit 1
fi
python3 jukebox_main.py --artist="$1" play
