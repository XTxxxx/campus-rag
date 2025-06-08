#!/bin/bash

DIR=${1:-.}

TOTAL_LINES=$(find "$DIR" -type f -name "*.py" -exec cat {} + | wc -l)

echo "Total lines of Python code in '$DIR': $TOTAL_LINES"
