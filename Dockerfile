FROM python:3.11.9-slim-bookworm AS builder

WORKDIR /app
RUN pip install -U pip
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Get service files
ADD lambda.py utils.py run.sh ./

# VERSION INFORMATION
ARG VERSION ???
ENV VERSION=$VERSION

# Command to run
ENV HOST=localhost
ENV PORT=8080
ENTRYPOINT ["./run.sh"]