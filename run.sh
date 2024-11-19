#!/bin/sh
echo "INFO     Pairwise sequence alignment - $VERSION"
fastapi run lambda.py --proxy-headers --host $HOST --port $PORT