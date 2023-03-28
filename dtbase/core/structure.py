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
    LargeBinary,
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


datatype_name = Enum("string", "float", "integer", "boolean", name="value_datatype")


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Locations


class Location(BASE):
    """
    This class describes all the physical locations in the digital twin.
    """

    __tablename__ = "location"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    schema_id = Column(
        Integer,
        ForeignKey("location_schema.id"),
        nullable=False,
    )

    # relationshionships (One-To-Many)
    string_values_relationship = relationship("LocationStringValue")
    integer_values_relationship = relationship("LocationIntegerValue")
    float_values_relationship = relationship("LocationFloatValue")
    boolean_values_relationship = relationship("LocationBooleanValue")

    # arguments
    __table_args__ = (UniqueConstraint("id"),)


class LocationIdentifier(BASE):
    """
    Variables that can be used to identify locations in the digital twin.
    """

    __tablename__ = "location_identifier"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    units = Column(String(100), nullable=True)
    datatype = Column(datatype_name, nullable=False)
    __table_args__ = (UniqueConstraint("name", "units"),)


class LocationSchema(BASE):
    """Types of locations."""

    __tablename__ = "location_schema"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    __table_args__ = (UniqueConstraint("name"),)


class LocationSchemaIdentifierRelation(BASE):
    """Relations on which location identifiers can and should be specified for which
    location schemas.
    """

    __tablename__ = "location_schema_identifier_relation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    schema_id = Column(
        Integer,
        ForeignKey("location_schema.id"),
        nullable=False,
    )
    identifier_id = Column(
        Integer,
        ForeignKey("location_identifier.id"),
        nullable=False,
    )
    __table_args__ = (UniqueConstraint("schema_id", "identifier_id"),)


class LocationStringValue(BASE):
    """
    The value of a string variable that can be used to identify locations in the digital
    twin.
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
    The value of an integer variable that can be used to identify locations in the
    digital twin.
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
    in the digital twin.
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
    The value of a boolean variable that can be used to identify locations in the
    digital twin.
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


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Sensors


class Sensor(BASE):
    """
    Class for sensors.
    """

    __tablename__ = "sensor"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    type_id = Column(Integer, ForeignKey("sensor_type.id"), nullable=False)
    unique_identifier = Column(String(100), nullable=False)
    name = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    # relationshionships (One-To-Many)
    string_values_relationship = relationship("SensorStringReading")
    integer_values_relationship = relationship("SensorIntegerReading")
    float_values_relationship = relationship("SensorFloatReading")
    boolean_values_relationship = relationship("SensorFloatReading")

    # arguments
    __table_args__ = (UniqueConstraint("unique_identifier"),)


class SensorMeasure(BASE):
    """
    Variables measured by sensors, e.g. temperature, pressure, electricity consumption.
    """

    __tablename__ = "sensor_measure"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    units = Column(String(100), nullable=True)
    datatype = Column(datatype_name, nullable=False)
    __table_args__ = (UniqueConstraint("name", "units"),)


class SensorType(BASE):
    """Types of sensors."""

    __tablename__ = "sensor_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    __table_args__ = (UniqueConstraint("name"),)


class SensorTypeMeasureRelation(BASE):
    """Relations on which sensor measures can and should have readings for which
    sensor types.
    """

    __tablename__ = "sensor_type_measure_relation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_id = Column(
        Integer,
        ForeignKey("sensor_type.id"),
        nullable=False,
    )
    measure_id = Column(
        Integer,
        ForeignKey("sensor_measure.id"),
        nullable=False,
    )
    __table_args__ = (UniqueConstraint("type_id", "measure_id"),)


class SensorStringReading(BASE):
    """
    Sensor reading of a string variable.
    """

    __tablename__ = "sensor_string_reading"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(Text, nullable=False)
    measure_id = Column(
        Integer,
        ForeignKey("sensor_measure.id"),
        nullable=False,
    )
    sensor_id = Column(
        Integer,
        ForeignKey("sensor.id"),
        nullable=False,
    )
    timestamp = Column(DateTime(), nullable=False)
    __table_args__ = (UniqueConstraint("measure_id", "sensor_id", "timestamp"),)


class SensorIntegerReading(BASE):
    """
    Sensor reading of a integer variable.
    """

    __tablename__ = "sensor_integer_reading"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(Integer, nullable=False)
    measure_id = Column(
        Integer,
        ForeignKey("sensor_measure.id"),
        nullable=False,
    )
    sensor_id = Column(
        Integer,
        ForeignKey("sensor.id"),
        nullable=False,
    )
    timestamp = Column(DateTime(), nullable=False)
    __table_args__ = (UniqueConstraint("measure_id", "sensor_id", "timestamp"),)


class SensorFloatReading(BASE):
    """
    Sensor reading of a float variable.
    """

    __tablename__ = "sensor_float_reading"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(Float, nullable=False)
    measure_id = Column(
        Integer,
        ForeignKey("sensor_measure.id"),
        nullable=False,
    )
    sensor_id = Column(
        Integer,
        ForeignKey("sensor.id"),
        nullable=False,
    )
    timestamp = Column(DateTime(), nullable=False)
    __table_args__ = (UniqueConstraint("measure_id", "sensor_id", "timestamp"),)


class SensorBooleanReading(BASE):
    """
    Sensor reading of a boolean variable.
    """

    __tablename__ = "sensor_boolean_reading"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(Boolean, nullable=False)
    measure_id = Column(
        Integer,
        ForeignKey("sensor_measure.id"),
        nullable=False,
    )
    sensor_id = Column(
        Integer,
        ForeignKey("sensor.id"),
        nullable=False,
    )
    timestamp = Column(DateTime(), nullable=False)
    __table_args__ = (UniqueConstraint("measure_id", "sensor_id", "timestamp"),)


class SensorLocation(BASE):
    """
    Location history of a sensor.
    """

    __tablename__ = "sensor_location"

    # columns
    id = Column(Integer, primary_key=True, autoincrement=True)

    sensor_id = Column(Integer, ForeignKey("sensor.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("location.id"), nullable=False)
    installation_datetime = Column(DateTime, nullable=False)
    time_created = Column(DateTime(), server_default=func.now())

    # arguments
    __table_args__ = (UniqueConstraint("sensor_id", "installation_datetime"),)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Other


class User(BASE, UserMixin):
    """
    Class for storing user credentials.
    """

    __tablename__ = "User"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(LargeBinary, nullable=False)

    time_created = Column(DateTime(), server_default=func.now())
    time_updated = Column(DateTime(), onupdate=func.now())

    def __init__(self, **kwargs):
        for prop, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, "__iter__") and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]
            setattr(self, prop, value)

    def __setattr__(self, prop, value):
        """Like setattr, but if the property we are setting is the password, hash it."""
        if prop == "password":
            value = hashpw(value.encode("utf8"), gensalt())
        super().__setattr__(prop, value)

    def __repr__(self):
        """
        Computes a string reputation of the object.
        """

        return str(self.username)
