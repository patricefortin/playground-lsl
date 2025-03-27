#!/bin/bash
find src/plsl -name "*.py" | entr ./bash-tools/kill-and-launch.sh