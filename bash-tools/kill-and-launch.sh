#!/bin/bash
cd "$(dirname "$0")"
cd ..

#
kill -s 1 $(ps -ef | grep __init__ | grep -v grep | awk '{print $2}')

# Launch in background to be able to run using `entr`
python src/plsl/__init__.py&