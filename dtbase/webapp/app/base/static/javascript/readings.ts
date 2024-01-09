export function updateSensorSelector(
  sensorIdsByType: { [key: string]: string[] },
  selectedSensor: string | null
): void {
  const sensorSelector = document.getElementById(
    "sensorSelector"
  ) as HTMLSelectElement;
  const sensorTypeSelector = document.getElementById(
    "sensorTypeSelector"
  ) as HTMLSelectElement;
  const selectedSensorType = sensorTypeSelector.value;

  // Empty sensorSelector
  while (sensorSelector.firstChild) {
    sensorSelector.removeChild(sensorSelector.firstChild);
  }

  // Create new options for the sensorSelector
  if (
    selectedSensorType != "" ||
    selectedSensorType !== null ||
    selectedSensor !== null ||
    selectedSensor != ""
  ) {
    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.selected = true;
    defaultOption.disabled = true;
    defaultOption.hidden = true;
    defaultOption.text = "Choose sensor";
    sensorSelector.appendChild(defaultOption);
  }

  if (selectedSensorType != "") {
    const sensorIds = sensorIdsByType[selectedSensorType];
    for (let i = 0; i < sensorIds.length; i++) {
      const option = document.createElement("option");
      const id = sensorIds[i];
      option.value = id;
      option.text = id;
      if (id == selectedSensor) option.selected = true;
      sensorSelector.appendChild(option);
    }
  }
}

declare global {
  interface Window {
    updateSensorSelector: (
      sensorIdsByType: { [key: string]: string[] },
      selectedSensor: string | null
    ) => void;
  }
}

window.updateSensorSelector = updateSensorSelector;
