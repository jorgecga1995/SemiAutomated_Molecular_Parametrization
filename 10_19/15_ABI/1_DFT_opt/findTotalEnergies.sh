#!/bin/bash

find . -type f -name "*.log" -exec awk -F'\\\\' '{for(i=1;i<=NF;i++) if($i ~ /^ETot=/) { n=split(FILENAME, path, "/"); print path[n] ": " $i }}' {} +

