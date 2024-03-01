from sqlalchemy.orm import Session

from dtbase.core.sensors import (
    insert_sensor,
    insert_sensor_measure,
    insert_sensor_readings,
    insert_sensor_type,
)

from .generate_synthetic_data import generate_trh_readings


def insert_trh_sensor(sensor_unique_id: str, session: Session) -> None:
    """
    Insert a temperature / relative humidity sensor.
    """
    try:
        insert_sensor_measure(
            name="Temperature",
            units="Degrees C",
            datatype="float",
            session=session,
        )
    except Exception:
        session.rollback()
    try:
        insert_sensor_measure(
            name="Humidity", units="Percent", datatype="float", session=session
        )
    except Exception:
        session.rollback()
    try:
        insert_sensor_type(
            name=sensor_unique_id,
            description="Temperature/Humidity",
            measures=[
                {"name": "Temperature", "units": "Degrees C", "datatype": "float"},
                {"name": "Humidity", "units": "Percent", "datatype": "float"},
            ],
            session=session,
        )
    except Exception:
        session.rollback()
    try:
        insert_sensor(
            type_name=sensor_unique_id,
            unique_identifier=sensor_unique_id,
            session=session,
        )
    except Exception:
        session.rollback()


def insert_trh_readings(
    session: Session,
    sensor_unique_id: str = "TRH1",
    insert_sensor: bool = True,
    add_noise: bool = True,
) -> None:
    """
    Insert a set of temperature and humidity readings for a sensor with
    unique_identifier 'TRH1'
    """
    if insert_sensor:
        try:
            insert_trh_sensor(sensor_unique_id, session)
        except Exception:
            print("Sensor already inserted")
            session.rollback()
    # generate the Temperature and Humidity readings
    readings = generate_trh_readings(sensor_ids=[1], add_noise=add_noise)
    # readings will be a pandas dataframe.
    # we want to extract some columns as lists, and convert timestamps to datetime
    timestamps = list(readings.timestamp)
    # warn=False disables a warning about losing nanosecond precision in the conversion
    timestamps = [t.to_pydatetime(warn=False) for t in timestamps]
    temps = list(readings.temperature)
    humids = list(readings.humidity)
    insert_sensor_readings(
        measure_name="Temperature",
        unique_identifier=sensor_unique_id,
        readings=temps,
        timestamps=timestamps,
        session=session,
    )
    insert_sensor_readings(
        measure_name="Humidity",
        unique_identifier=sensor_unique_id,
        readings=humids,
        timestamps=timestamps,
        session=session,
    )
    try:
        session.commit()
        print(f"Inserted {len(temps)} temperature values")
    except Exception:
        session.rollback()
        print(f"Failed to insert {len(temps)} temperature values")
