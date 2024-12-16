FROM python:3.11.9-slim-bookworm AS builder

WORKDIR /app

# Update package list and ensure we have git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN pip install -U pip
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Get service files
ADD service.py utils.py ./

# VERSION INFORMATION
ARG VERSION ???
ENV VERSION=$VERSION

# Command to run
ENV HOST=0.0.0.0
ENV PORT=8080
ENTRYPOINT ["python",  "service.py"]