import { initialiseDataTable } from "./datatables";
import { Sensor } from "./interfaces";

interface ArgType {
  [key: string]: Sensor[];
}

export function updateSensorTable(sensors_for_each_type: ArgType): void {
  try {
    const selectedSensorType = (
      document.getElementById("sensor_type") as HTMLSelectElement
    ).value;
    const sensorTableWrapper = document.getElementById(
      "sensorTableWrapper"
    ) as HTMLDivElement;
    if (!selectedSensorType) {
      sensorTableWrapper.innerHTML = "";
      return;
    }

    const sensors = sensors_for_each_type[selectedSensorType];
    let tableContent = "";

    // Construct the table headers
    tableContent += "<thead><tr><th class='num-column' scope='col'>#</th>"; // Adding '#' column
    for (const key in sensors[0]) {
      if (key !== "id") {
        // Exclude 'id' column
        tableContent += `<th scope='col'>${key}</th>`;
      }
    }
    tableContent += "</tr></thead>";

    // Construct the table body
    tableContent += "<tbody>";
    for (let i = 0; i < sensors.length; i++) {
      tableContent += "<tr><td class='num-column'>" + (i + 1) + "</td>"; // Adding row number
      for (const key in sensors[i]) {
        if (key !== "id") {
          // Exclude 'id' column
          const value = (sensors[i] as any)[key];
          tableContent += `<td>${value}</td>`;
        }
      }
      tableContent += "</tr>";
    }
    tableContent += "</tbody>";

    // Construct the full table and inject it into the DOM
    const fullTable = `<table id="datatable" class="table table-striped table-hover nowrap" style="width:100%">${tableContent}</table>`;

    sensorTableWrapper.innerHTML = fullTable;
    initialiseDataTable("#datatable");
  } catch (error) {
    console.error(error);
  }
}

declare global {
  interface Window {
    updateSensorTable: (sensors_for_each_type: ArgType) => void;
  }
}

window.updateSensorTable = updateSensorTable;
