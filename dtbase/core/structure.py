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


class LocationClass(BASE):
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


class LocationStringIdentifierClass(BASE):
    """
    Any string variables that can be used to identify locations in the farm.
    """

    __tablename__ = "location_string_variable"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    units = Column(String(100), nullable=True)
    __table_args__ = (UniqueConstraint("name", "units"),)


class LocationIntegerIdentifierClass(BASE):
    """
    Any integer variables that can be used to identify locations in the farm.
    """

    __tablename__ = "location_integer_variable"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    units = Column(String(100), nullable=True)
    __table_args__ = (UniqueConstraint("name", "units"),)


class LocationFloatIdentifierClass(BASE):
    """
    Any floating point number variables that can be used to identify locations in the
    farm.
    """

    __tablename__ = "location_float_variable"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    units = Column(String(100), nullable=True)
    __table_args__ = (UniqueConstraint("name", "units"),)


class LocationBooleanIdentifierClass(BASE):
    """
    Any boolean variables that can be used to identify locations in the farm.
    """

    __tablename__ = "location_float_variable"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    units = Column(String(100), nullable=True)
    __table_args__ = (UniqueConstraint("name", "units"),)


class LocationStringValueClass(BASE):
    """
    The value of a string variable that can be used to identify locations in the farm.
    """

    __tablename__ = "location_string_value"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(String(100), nullable=False)
    variable_id = Column(
        Integer,
        ForeignKey("location_string_variable.id"),
        nullable=False,
    )
    location_id = Column(
        Integer,
        ForeignKey("location.id"),
        nullable=False,
    )
    __table_args__ = (UniqueConstraint("variable_id", "location_id"),)


class LocationIntegerValueClass(BASE):
    """
    The value of an integer variable that can be used to identify locations in the farm.
    """

    __tablename__ = "location_integer_value"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(Integer, nullable=False)
    variable_id = Column(
        Integer,
        ForeignKey("location_integer_variable.id"),
        nullable=False,
    )
    location_id = Column(
        Integer,
        ForeignKey("location.id"),
        nullable=False,
    )
    __table_args__ = (UniqueConstraint("variable_id", "location_id"),)


class LocationFloatValueClass(BASE):
    """
    The value of a floating point number variable that can be used to identify locations
    in the farm.
    """

    __tablename__ = "location_float_value"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(Float, nullable=False)
    variable_id = Column(
        Integer,
        ForeignKey("location_float_variable.id"),
        nullable=False,
    )
    location_id = Column(
        Integer,
        ForeignKey("location.id"),
        nullable=False,
    )
    __table_args__ = (UniqueConstraint("variable_id", "location_id"),)


class LocationBooleanValueClass(BASE):
    """
    The value of a boolean variable that can be used to identify locations in the farm.
    """

    __tablename__ = "location_boolean_value"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(Boolean, nullable=False)
    variable_id = Column(
        Integer,
        ForeignKey("location_boolean_variable.id"),
        nullable=False,
    )
    location_id = Column(
        Integer,
        ForeignKey("location.id"),
        nullable=False,
    )
    __table_args__ = (UniqueConstraint("variable_id", "location_id"),)
