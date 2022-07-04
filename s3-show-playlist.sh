#!/bin/sh
if [ $# -eq 0 ] ; then
   echo "error: missing playlist name"
   echo 'example: ./s3-show-playlist.sh "CrankItUp"'
   exit 1
fi
python3 jukebox_main.py --storage s3 --playlist="$1" show-playlist 
