from typing import Optional

from pydantic import BaseModel, RootModel

ValueTypes = float | bool | int | str


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


Coordinates = RootModel[dict[str, ValueTypes]]


class LocationSchemaIdentifier(BaseModel):
    schema_name: str
