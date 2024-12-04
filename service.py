from typing import ClassVar, List
from fastapi import FastAPI
from pydantic import Field
from signal import signal, SIGTERM
import sys
import os
from Bio import Align

from utils import IVCAPRestService, IVCAPService, SchemaModel, StrEnum

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

@app.post("/")
def root(req: Request) -> Response:
    p = req.model_dump(exclude=["target", "query", "aspect_schema"])
    aligner = Align.PairwiseAligner(**p)
    r = aligner.align(req.target, req.query)
    alignments=[a.aligned.tolist() for a in r]
    res = Response(target=req.target, query=req.query, alignments=alignments, score=r.score)
    return res

# Allows platform to check if everything is OK
@app.get("/_healtz")
def healtz():
    return {"version": os.environ.get("VERSION", "???")}
