from dtbase.core.structure import (
    Location,
    LocationBooleanValue,
    LocationFloatValue,
    LocationIdentifier,
    LocationIntegerValue,
    LocationSchema,
    LocationSchemaIdentifierRelation,
    LocationStringValue,
)


def get_value_class_from_instance_type(value):
    value_class = (
        LocationBooleanValue
        if isinstance(value, bool)
        else LocationFloatValue
        if isinstance(value, float)
        else LocationIntegerValue
        if isinstance(value, int)
        else LocationStringValue
        if isinstance(value, str)
        else None
    )
    return value_class


def get_value_class_from_type_name(name):
    value_class = (
        LocationBooleanValue
        if name == "bool"
        else LocationFloatValue
        if name == "float"
        else LocationIntegerValue
        if name == "int"
        else LocationStringValue
        if name == "string"
        else None
    )
    return value_class
