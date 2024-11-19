# IVCAP "FastAPI" Service Demo

This repo template contains a very simplistic implementation of a
pairwise sequence alignment service based on the respective implementation in
the [BioPython](https://biopython.org/) package.

A "lambda" service expects to be called on one or maybe more HTTP endpoints, performs
some action and returns a result.

There is no guarantee that any follow-up requests are being handled by
the same instance. Therefore, any potential state needs to be either
carried in the request, or stored in IVCAP's Datafabric.

* [Getting started](#getting-started)
* [Implementation](#implementation)
* [Deployment](#deploying-deployment)

## Getting Started <a name="#getting-started"></a>

First, we need to setup a Python environment. We are using `conda`, but `venv` is
also a widely used alternative

```
conda create --name my-service python=3.11 -y
conda activate my-service
pip install -r requirements.txt
```

To test the service, run the `make run` target.

```
% make run
env VERSION="|f097e6d|2024-11-19T15:50+11:00" HOST=localhost PORT=8096 \
                ./run.sh
INFO     Pairwise sequence alignment - |f097e6d|2024-11-19T15:50+11:00
INFO     Using path lambda.py
...
INFO:     Started server process [67746]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8096 (Press CTRL+C to quit)
```

Now open another terminal and call the service. We already provide a sample request
in [example-req.json](./example-req.json)

```
% make submit-request
curl -i -X POST -H "Content-Type: application/json" -d @example-req.json http://localhost:8096
HTTP/1.1 200 OK
date: Tue, 19 Nov 2024 04:54:01 GMT
server: uvicorn
content-length: 171
content-type: application/json

{
  "$schema":"urn:sd.test:schema.fastapi-test.response.1",
  "target":"GAAT",
  "query":"GAT",
  "alignments":[[[[0,2],[3,4]],[[0,2],[2,3]]],[[[0,1],[2,4]],[[0,1],[1,3]]]],
  "score":3.0
}
```


## Implementation <a name="implementation"></a>

This service is a thin wrapper over BioPython's `Align.PairwiseAligner`.

* [lambda.py](#lambda.py)
* [utils.py](#utils.py)
* [Dockerfile](#dockerfile)


### [lambda.py](.lambda.py]) <a name="lambda.py"></a>

For the service itself we are using [fastAPI](https://fastapi.tiangolo.com/).

The code in [lambda.py](lambda.py) falls into the following parts:

#### Import packages

```
from typing import ClassVar, List
from fastapi import FastAPI
from pydantic import Field
from signal import signal, SIGTERM
import sys
import os
from Bio import Align

from utils import IVCAPRestService, IVCAPService, SchemaModel, StrEnum
```

#### Setting up a graceful shutdown for kubernetes deployments

```
signal(SIGTERM, lambda _1, _2: sys.exit(0))
```

#### Service description and general `fastAPI` setup

```
title = "Pairwise sequence alignment"
summary = "Aligs two sequences to each other by optimizing the similarity score between them.",
description = """..."""

app = FastAPI(
    title=title,
    description=description,
    summary=summary,
    ...
```

#### Defining the service's Request and Response

To support discover and automatic adaptation to what a service expects
as well as produces, we need to properly define the "shape" of the
expected request and the produced response.

In this implementation we take advantage of the power the [Pydantic](https://docs.pydantic.dev/latest/)
library.

```
class ModeE(StrEnum):
    Global = "global"
    Local = "local"
    Fogsaa = "fogsaa"

class Request(SchemaModel):
    SCHEMA: ClassVar[str] = "urn:sd.test:schema.fastapi-test.request.1"
    target: str = Field(description="The target sequence as a string", examples="GAACT")
    query: str = Field(description="The sequence to align as a string", examples="GAT")
    mode: ModeE = Field(ModeE.Local, description="Some decription on what a 'mode' means")
    match_score: float = Field(1.000000, description="Some decription on what a 'match_score' means")
    mismatch_score: float = Field(0.000000, description="Some decription on what a 'mismatch_score' means")

class Response(SchemaModel):
    SCHEMA: ClassVar[str] = "urn:sd.test:schema.fastapi-test.result.1"
    target: str = Field(description="The target sequence as a string", examples="GAACT")
    query: str = Field(description="The sequence to align as a string", examples="GAT")
    alignments: List[List[List[List[int]]]] = Field(description="a list of alignments")
    score: float = Field(description="Overall score of the alignemnt?")
```

> Please note that we define a `SCHEMA` class var for every dataclass to be used in the
JSON schema we will need when registering this service with IVCAP

#### Defining the IVCAP service definition

The following instance doe not necessarily be defined in the service file as it is only
being used when registering hte service with IVCAP. However, for simplicity
```
Service = IVCAPService(
    name=title,
    description=description,
    controller=IVCAPRestService(
        request=Request,
        response=Response,
    ),
)
```

#### The main entry point

```
@app.post("/")
def root(req: Request) -> Response:
    p = req.model_dump(exclude=["target", "query", "aspect_schema"])
    aligner = Align.PairwiseAligner(**p)
    r = aligner.align(req.target, req.query)
    alignments=[a.aligned.tolist() for a in r]
    res = Response(target=req.target, query=req.query, alignments=alignments, score=r.score)
    return res
```

#### And finally, the _Health_ indicator needed by Kubernetes

```
@app.get("/_healtz")
def healtz():
    return {"version": os.environ.get("VERSION", "???")}
```

To test the service, first run `make install` (ideally within a `venv` or `conda` environment) beforehand to install the necessary dependencies. Then `make run` will start the service listing on [http://0.0.0.0:8080](http://0.0.0.0:8080).

### [utils.py](./utils.py) <a name="utils.py"></a>

This file contains a few helper functions and classes which hopefully helps
in more systematically define different aspects of a service as well as
then automatically generate additional "artifacts" needed to deploy the service
in different contexts

### [Dockerfile](./Dockerfile) <a name="dockerfile"></a>

This file describes a simple configuration for building a docker image for
this service. The make target `make docker-build` will build the image, and
the `make docker-publish` target will upload it to IVCAP.

To test the created docker package, run `make docker-run`:

```
docker run -it \
                -p 8096:8080 \
                --user "502:20" \
                --platform=linux/amd64 \
                --rm \
                pairwise_sequence_alignment:latest
INFO     Pairwise sequence alignment - |f097e6d|2024-11-19T14:59+11:00
INFO     Using path lambda.py
INFO     Resolved absolute path /app/lambda.py
...
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

And as mentioned above, you can send a request to this service with the `make submit-request` target.

## Deploying <a name="deploying"></a>

Coming soon ...