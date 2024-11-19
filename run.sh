#!/bin/sh
echo "INFO     Pairwise sequence alignment - $VERSION"
fastapi run service.py --proxy-headers --host $HOST --port $PORT