from typing import Optional

from pydantic import BaseModel, RootModel

ValueType = float | bool | int | str


class MessageResponse(BaseModel):
    detail: str


class UserIdentifier(BaseModel):
    email: str


class LoginCredentials(BaseModel):
    email: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str


class ParsedToken(BaseModel):
    sub: str
    exp: int
    token_type: str


class LocationIdentifier(BaseModel):
    name: str
    units: Optional[str]
    datatype: str


class LocationSchema(BaseModel):
    name: str
    description: Optional[str]
    identifiers: list[LocationIdentifier]


Coordinates = RootModel[dict[str, ValueType]]


class LocationSchemaIdentifier(BaseModel):
    schema_name: str


class Model(BaseModel):
    name: str


class ModelScenario(BaseModel):
    model_name: str
    description: Optional[str]


class ModelMeasure(BaseModel):
    name: str
    units: str
    datatype: str


class SensorMeasure(BaseModel):
    name: str
    units: str
    datatype: str
