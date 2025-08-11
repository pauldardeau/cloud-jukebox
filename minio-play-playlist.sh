#!/bin/sh
if [ $# -eq 0 ] ; then
   echo "error: missing playlist name"
   echo 'example: ./minio-play-playlist.sh "CrankItUp"'
   exit 1
fi
python3 jukebox_main.py --storage minio --playlist="$1" play-playlist 
