#!/bin/sh
if [ $# -eq 0 ] ; then
   echo "error: missing artist name"
   exit 1
fi
python jukebox_main.py --artist="$1" play
