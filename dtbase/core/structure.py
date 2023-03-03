"""
Module to define the structure of the database. Each Class, defines a table in the
database.
    __tablename__: creates the table with the name given
    __table_args__: table arguments eg: __table_args__ = {'sqlite_autoincrement': True}
    BASE: the declarative_base() callable returns a new base class from which all mapped
    classes should inherit. When the class definition is completed, a new Table and
    mapper() is generated.
"""
import enum

from bcrypt import gensalt, hashpw
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import false

SQLA = SQLAlchemy()
BASE = SQLA.Model


class Location(BASE):
    """
    This class describes all the physical locations in the farm.
    """

    __tablename__ = "location"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)

    # relationshionships (One-To-Many)
    string_values_relationship = relationship("LocationStringValueClass")
    integer_values_relationship = relationship("LocationIntegerValueClass")
    float_values_relationship = relationship("LocationFloatValueClass")

    # arguments
    __table_args__ = (UniqueConstraint("id"),)


class LocationIdentifier(BASE):
    """
    Any string variables that can be used to identify locations in the farm.
    """

    __tablename__ = "location_string_identifier"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    units = Column(String(100), nullable=True)
    datatype = Column(Enum("string", "float", "integer", "boolean"), nullable=False)
    __table_args__ = (UniqueConstraint("name", "units"),)


class LocationStringValue(BASE):
    """
    The value of a string variable that can be used to identify locations in the farm.
    """

    __tablename__ = "location_string_value"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(Text, nullable=False)
    identifier_id = Column(
        Integer,
        ForeignKey("location_identifier.id"),
        nullable=False,
    )
    location_id = Column(
        Integer,
        ForeignKey("location.id"),
        nullable=False,
    )
    __table_args__ = (UniqueConstraint("identifier_id", "location_id"),)


class LocationIntegerValue(BASE):
    """
    The value of an integer variable that can be used to identify locations in the farm.
    """

    __tablename__ = "location_integer_value"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(Integer, nullable=False)
    identifier_id = Column(
        Integer,
        ForeignKey("location_identifier.id"),
        nullable=False,
    )
    location_id = Column(
        Integer,
        ForeignKey("location.id"),
        nullable=False,
    )
    __table_args__ = (UniqueConstraint("identifier_id", "location_id"),)


class LocationFloatValue(BASE):
    """
    The value of a floating point number variable that can be used to identify locations
    in the farm.
    """

    __tablename__ = "location_float_value"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(Float, nullable=False)
    identifier_id = Column(
        Integer,
        ForeignKey("location_identifier.id"),
        nullable=False,
    )
    location_id = Column(
        Integer,
        ForeignKey("location.id"),
        nullable=False,
    )
    __table_args__ = (UniqueConstraint("identifier_id", "location_id"),)


class LocationBooleanValue(BASE):
    """
    The value of a boolean variable that can be used to identify locations in the farm.
    """

    __tablename__ = "location_boolean_value"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(Boolean, nullable=False)
    identifier_id = Column(
        Integer,
        ForeignKey("location_identifier.id"),
        nullable=False,
    )
    location_id = Column(
        Integer,
        ForeignKey("location.id"),
        nullable=False,
    )
    __table_args__ = (UniqueConstraint("identifier_id", "location_id"),)


class LocationSchema(BASE):
    """Types of locations."""

    __tablename__ = "location_schema"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    __table_args__ = (UniqueConstraint("name"),)


class LocationSchemaIdentifiers(BASE):
    """Relations on which location identifiers can and should be specified for which
    location schemas.
    """

    __tablename__ = "location_schema_identifiers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    location_schema_id = Column(
        Integer,
        ForeignKey("location_schema.id"),
        nullable=False,
    )
    location_identifier_id = Column(
        Integer,
        ForeignKey("location_identifier.id"),
        nullable=False,
    )
