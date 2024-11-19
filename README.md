# IVCAP "Lambda" Service Demo

This repo template contains a very simplistic implementation of a
"lambda" service. A "lambda" service expects to be called on
one or more HTTP endpoints, performs some action and returns a result.
There is no guarantee that any follow-up requests are being handled by
the same instance. Therefore, any potential state needs to be either
carried in the request, or stored in IVCAP's Datafabric.

## Implementation

This service Joseph Weizenbaum's famous Eliza chat bot as a service. Eliza
doesn't keep any state between rounds of questions and therefore perfectly
matches our constraints.

The actual Eliza implementation is copied from [Wade Brainerd's](http://wadeb.com/)
['eliza' repo](https://github.com/wadetb/eliza) into [./eliza](./eliza).

### [lambda.py](.lambda.py])

For the service itself we are using [fastAPI](https://fastapi.tiangolo.com/).

The code in [lambda.py](lambda.py) falls into the following parts:

#### Import packages

```
from fastapi import FastAPI
from eliza import eliza
from signal import signal, SIGTERM
import sys
import os
```

#### Setting up a graceful shutdown for kubernetes deployments

```
signal(SIGTERM, lambda _1, _2: sys.exit(0))
```

#### Service description and general `fastAPI` setup

```
description = """
Chat with Eliza Service. 🚀
...
"""

app = FastAPI(
    title="Chat With Eliza",
    description=description,
    summary="Implementation of Joseph Weizenbaum's famous Eliza chat-bot.",
    version=os.environ.get("VERSION", "???"),
    ...
```

#### Initialising the Eliza _Doctor_

```
eliza = eliza.Eliza()
eliza.load('eliza/doctor.txt')
```

#### The main entry point

```
@app.post("/")
def root(said: str):
    response = eliza.respond(said)
    return {
        "input": said,
        "response": response
    }
```

#### And finally, the _Health_ indicator needed by Kubernetes

```
@app.get("/_healtz")
def healtz():
    return {"version": os.environ.get("VERSION", "???")}
```

To test the service, first run `make install` (ideally within a `venv` or `conda` environment) beforehand to install the necessary dependencies. Then `make run` will start the service listing on [http://0.0.0.0:8080](http://0.0.0.0:8080).

### [service.json](./service.json)

This file describes the service as needed for the `ivcap service create ...` command.

> The format is still in flux and we most likely going to reference
the approprite section in the [IVCAP Docs](https://ivcap-works.github.io/ivcap-docs/).

### [Dockerfile](./Dockerfile)

This file describes a simple configuration for building a docker image for
this service. The make target `make docker-build` will build the image, and
the `make docker-publish` target will upload it to IVCAP.

## Deploying

```
% make service-register
Building docker image chat_with_eliza
docker build \
                -t chat_with_eliza:latest \
                --platform=linux/amd64 \
                --build-arg VERSION="v0.1.0|a2db1d4|2024-08-20T14:49+10:00" \
                -f /Users/ott030/src/IVCAP/Services/ivcap-python-lambda-service/Dockerfile \
                /Users/ott030/src/IVCAP/Services/ivcap-python-lambda-service
[+] Building 1.8s (13/1 FINISHED                           docker:desktop-linux
 => [internal] load build definition from Dockerfile                       0.0s
 => => transferring dockerfile: 415B                                       0.0s
 ...
 => => naming to docker.io/library/                                        0.0s

Finished building docker image chat_with_eliza

Publishing docker image 'chat_with_eliza:a2db1d4'
 Pushing chat_with_eliza:a2db1d4 from local, may take multiple minutes depending on the size of the image ...
 74b9a56f90      31.09MB uploaded
 67d49562f2       3.73MB uploaded
 ...
 45a06508-5c3a-4678-8e6d-e6399bf27538/chat_with_eliza:a2db1d4 pushed
<<<<<<< HEAD
 74b9a56f90 31.09MB 31.09MB server uploading'
=======
>> Successfully published 'chat_with_eliza:67e2ba4' as '45a06508-5c3a-4678-8e6d-e6399bf27538/chat_with_eliza:67e2ba4'
cat /Users/ott030/src/IVCAP/Services/ivcap-python-lambda-service/service.json \
        | sed 's|#DOCKER_TAG#|45a06508-5c3a-4678-8e6d-e6399bf27538/chat_with_eliza:67e2ba4|' \
        | sed 's|#SERVICE_ID#|urn:ivcap:service:4ebd0208-8328-5d69-8c44-ec50939c0967|' \
  | ivcap aspect update urn:ivcap:service:4ebd0208-8328-5d69-8c44-ec50939c0967 -f - --timeout 600
{
  "id": "urn:ivcap:aspect:5f9ade14-a4d0-4df4-9b16-d284edb6d3f5"
}
```
>>>>>>> main
