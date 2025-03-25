#!/bin/bash
find src -name "*.py" | entr ./bash-tools/kill-and-launch.sh