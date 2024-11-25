from enum import Enum
from typing import ClassVar, List, TypeVar, Type as TypeT
from pydantic import BaseModel, Field, TypeAdapter, field_serializer, model_validator

class StrEnum(str, Enum):
    def __repr__(self) -> str:
        return str.__repr__(self.value)

class SchemaModel(BaseModel):
    aspect_schema: str = Field(None, alias="$schema")

    @classmethod
    def json_schema(cls, *, json_schema="https://json-schema.org/draft/2020-12/schema"):
        if not hasattr(cls, 'SCHEMA'):
            raise Exception("Missing 'SCHEMA' declaration")
        s = {
            "$schema": json_schema,
            "$id": cls.SCHEMA,
        }
        if hasattr(cls, 'DESCRIPTION'):
            s["description"] = cls.DESCRIPTION
        t = TypeAdapter(cls)
        s.update(t.json_schema())
        s["properties"].pop("$schema")
        return s

    @model_validator(mode='after')
    def set_aspect_schema(self) -> "SchemaModel":
        if not hasattr(self.__class__, 'SCHEMA'):
            raise Exception("Missing 'SCHEMA' declaration")
        self.aspect_schema = self.__class__.SCHEMA
        return self

T = TypeVar('T', bound=SchemaModel)
U = TypeVar('U', bound=SchemaModel)

class IVCAPRestService(SchemaModel):
    SCHEMA: ClassVar[str] = "urn:ivcap:schema.service.rest.1"

    package_urn: str = Field("#PACKAGE_URN#", description="IVCAP package implementing this service")
    command: List[str] = Field(description="list of comand and paramters to start the service inside the container")
    port: int = Field(80, description="port this service is listening on")
    readyPath: str = Field(description="GET path of the service to use for verifying if the service is up and ready",
                           serialization_alias="ready_path")

    request: TypeT[T] = Field(description="dataclass describing shape of request")
    response: TypeT[U] = Field(description="dataclass describing shape of response")

    @field_serializer("request", return_type=dict)
    @staticmethod
    def serialize_request(request: TypeT[T]) -> dict:
        return request.json_schema()

    @field_serializer("response", return_type=dict)
    @staticmethod
    def serialize_response(response: TypeT[U]) -> dict:
        return response.json_schema() # "response"

class IVCAPService(SchemaModel):
    SCHEMA: ClassVar[str] = "urn:ivcap:schema.service.2"
    id: str = Field("#SERVICE_URN#", description="IVCAP service URN", alias="$id")
    name: str = Field(description="human friendly name of service",)
    description: str = Field(description="a more detailed description of the service",)
    # parameters: []
    policy: str = Field("urn:ivcap:policy:ivcap.base.service", description="")
    # controller_schema will be automatically inserted depending on the controller class used
    controller_schema: str = Field(None, description="schema of the specific controller required")
    controller: IVCAPRestService

    @model_validator(mode='after')
    def set_controller_schema(self) -> "SchemaModel":
        self.controller_schema = self.controller.aspect_schema
        return self