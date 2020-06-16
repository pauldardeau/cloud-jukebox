#!/bin/sh
if [ $# -eq 0 ]; then
   echo "error: missing song identifier"
   exit 1
fi
python jukebox_main.py --song $1 delete-song
