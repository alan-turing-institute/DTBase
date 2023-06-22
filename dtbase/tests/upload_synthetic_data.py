from dtbase.core.locations import (
    insert_location_schema,
    insert_location_identifier,
    insert_location,
)

from dtbase.core.sensors import (
    insert_sensor_measure,
    insert_sensor_type,
    insert_sensor,
    insert_sensor_readings,
)


from dtbase.tests.generate_synthetic_data import (
    generate_trh_readings,
    generate_weather,
    generate_weather_forecast,
)


def insert_trh_sensor(sensor_unique_id, session):
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
    except:
        session.rollback()
    try:
        insert_sensor_measure(
            name="Humidity", units="Percent", datatype="float", session=session
        )
    except:
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
    except:
        session.rollback()
    try:
        insert_sensor(
            type_name=sensor_unique_id,
            unique_identifier=sensor_unique_id,
            session=session,
        )
    except:
        session.rollback()


def insert_trh_readings(session, sensor_unique_id="TRH1", insert_sensor=True):
    """
    Insert a set of temperature and humidity readings for a sensor
    with unique_identifier 'TRH1'
    """
    if insert_sensor:
        try:
            insert_trh_sensor(sensor_unique_id, session)
        except:
            print("Sensor already inserted")
            session.rollback()
    # generate the Temperature and Humidity readings
    readings = generate_trh_readings(sensor_ids=[1])
    # readings will be a pandas dataframe.
    # we want to extract some columns as lists, and convert timestamps to datetime
    timestamps = list(readings.timestamp)
    timestamps = [t.to_pydatetime() for t in timestamps]
    temps = list(readings.temperature)
    humids = list(readings.humidity)
    insert_sensor_readings(
        measure_name="Temperature",
        sensor_uniq_id=sensor_unique_id,
        readings=temps,
        timestamps=timestamps,
        session=session,
    )
    insert_sensor_readings(
        measure_name="Humidity",
        sensor_uniq_id=sensor_unique_id,
        readings=humids,
        timestamps=timestamps,
        session=session,
    )
    try:
        session.commit()
    except:
        session.rollback()
    print(f"Inserted {len(temps)} temperature values")
