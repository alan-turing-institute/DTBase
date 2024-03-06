export interface LocationIdentifier {
  id: number;
  name: string;
  datatype: string;
  units: string;
}

export interface LocationSchema {
  id: number;
  name: string;
  description: string;
  identifiers: LocationIdentifier[];
}

export interface Location {
  id: number;
  [key: string]: number | string | boolean;
}

export interface ModelScenario {
  id: number;
  model_id: number;
  model_name: string;
  description: string | null;
}

export interface TimeseriesDataPoint<T> {
  timestamp: string;
  value: T;
}

export interface Sensor {
  id: number;
  name: string;
  notes: string;
  sensor_type_id: number;
  sensor_type_name: string;
  unique_identifier: string;
}

export interface SensorMeasure {
  datatype: string;
  id: number;
  name: string;
  units: string;
}
