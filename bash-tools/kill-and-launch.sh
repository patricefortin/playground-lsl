#!/bin/bash
cd "$(dirname "$0")"
cd ..

SCRIPT_PATH="src/plsl/gui.py"

#
kill -s 1 $(ps -ef | grep "$SCRIPT_PATH" | grep -v grep | awk '{print $2}')

# Launch in background to be able to run using `entr`
python $SCRIPT_PATH &