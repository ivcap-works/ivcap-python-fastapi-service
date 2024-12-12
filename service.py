from time import sleep
from typing import ClassVar, List
from fastapi import FastAPI
from pydantic import Field
import argparse
from signal import signal, SIGTERM
import sys
import os
import random
import string

from Bio import Align

from utils import SchemaModel, StrEnum

# shutdown pod cracefully
signal(SIGTERM, lambda _1, _2: sys.exit(0))

title = "Pairwise sequence alignment"
summary = "Aligs two sequences to each other by optimizing the similarity score between them."
description = """
Pairwise sequence alignment

Pairwise sequence alignment is the process of aligning two sequences to each other by optimizing the similarity
score between them. This service supports for global and local alignments
using the Needleman-Wunsch, Smith-Waterman, Gotoh (three-state), and Waterman-Smith-Beyer global and local
pairwise alignment algorithms, with numerous options to change the alignment parameters.
We refer to Durbin et al. [Durbin1998] for in-depth information on sequence alignment algorithms.

This service is essentially a thin wrapper over the "pairwise sequence alignment' implementation
found in the [BioPython](https://biopython.org/) package.
"""

app = FastAPI(
    title=title,
    description=description,
    summary=summary,
    version=os.environ.get("VERSION", "???"),
    contact={
        "name": "Max Ott",
        "email": "max.ott@data61.csiro.au",
    },
    license_info={
        "name": "Biopython",
        "url": "https://github.com/biopython/biopython/blob/master/LICENSE.rst",
    },
    docs_url="/docs", # ONLY set when there is no default GET
)

# Add support for JSON-RPC invocation (https://www.jsonrpc.org/)
from ivcap_fastapi import use_json_rpc_middleware
use_json_rpc_middleware(app)

parser = argparse.ArgumentParser(description=title)
parser.add_argument('--host', type=str, default=os.environ.get("HOST", "localhost"), help='Host address')
parser.add_argument('--port', type=int, default=os.environ.get("PORT", "8080"), help='Port number')

parser.add_argument('--delay', type=int, default=5, help='Run in async mode, pretending that processing takes this many seconds')

args = parser.parse_args()
delay = args.delay

class ModeE(StrEnum):
    Global = "global"
    Local = "local"
    Fogsaa = "fogsaa"

class Request(SchemaModel):
    SCHEMA: ClassVar[str] = "urn:sd.test:schema.fastapi-test.request.1"
    target: str = Field(description="The target sequence as a string", examples=["GAACT"])
    query: str = Field(description="The sequence to align as a string", examples=["GAT"])
    mode: ModeE = Field(ModeE.Local, description="Some decription on what a 'mode' means")
    match_score: float = Field(1.000000, description="Some decription on what a 'match_score' means")
    mismatch_score: float = Field(0.000000, description="Some decription on what a 'mismatch_score' means")

class Response(SchemaModel):
    SCHEMA: ClassVar[str] = "urn:sd.test:schema.fastapi-test.response.1"
    target: str = Field(description="The target sequence as a string", examples=["GAACT"])
    query: str = Field(description="The sequence to align as a string", examples=["GAT"])
    alignments: List[List[List[List[int]]]] = Field(description="a list of alignments")
    score: float = Field(description="Overall score of the alignemnt?")

def work(req: Request) -> Response:
    p = req.model_dump(exclude=["target", "query", "aspect_schema"])
    aligner = Align.PairwiseAligner(**p)
    r = aligner.align(req.target, req.query)
    alignments=[a.aligned.tolist() for a in r]
    return Response(target=req.target, query=req.query, alignments=alignments, score=r.score)

#####
# Calculate alingment and return result  immedaitely

@app.post("/immediate")
def immediate(req: Request) -> Response:
    return work(req)

@app.post("/test")
def testf(req: dict) -> str:
    return req.get("method")

#####
# Simulate dispatched calculation by immediately returning
# a reference to a different "Location" to later pick up the
# result

from ivcap_fastapi import TryLaterException, use_try_later_middleware
use_try_later_middleware(app)

jobs = {}

@app.post("/delayed")
def delayed(req: Request) -> Response:
    jobID = ''.join(random.choice(string.ascii_letters) for i in range(10))
    jobs[jobID] = req
    raise TryLaterException(f"/jobs/{jobID}", delay)

@app.get("/jobs/{jobID}")
def get_job(jobID: str) -> Response:
    req = jobs[jobID]
    return work(req)

#####
# Simulate a long running calculation.

@app.post("/long")
def immediate(req: Request) -> Response:
    sleep(delay)
    return work(req)


# Allows platform to check if everything is OK
@app.get("/_healtz")
def healtz():
    return {"version": os.environ.get("VERSION", "???")}

if __name__ == "__main__":
    import uvicorn
    print(f"INFO:     {title} - {os.getenv('VERSION')}")
    if delay > 0: print(f"INFO:     Operating with artifical delay of {delay} sec")
    uvicorn.run(app, host=args.host, port=args.port)