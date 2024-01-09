import { initialiseDataTable } from "./datatables";
import { Sensor } from "./interfaces";

interface ArgType {
  [key: string]: Sensor[];
}

export function updateTable(sensors_for_each_type: ArgType): void {
  try {
    const selectedSensorType = (
      document.getElementById("sensor_type") as HTMLSelectElement
    ).value;
    if (!selectedSensorType) {
      document.getElementById("sensorTableWrapper").innerHTML = "";
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
          tableContent += `<td>${sensors[i][key]}</td>`;
        }
      }
      tableContent += "</tr>";
    }
    tableContent += "</tbody>";

    // Construct the full table and inject it into the DOM
    const fullTable = `<table id="datatable" class="table table-striped table-hover nowrap" style="width:100%">${tableContent}</table>`;

    document.getElementById("sensorTableWrapper").innerHTML = fullTable;
    initialiseDataTable("#datatable");
  } catch (error) {
    console.error(error);
  }
}

declare global {
  interface Window {
    updateTable: (sensors_for_each_type: ArgType) => void;
  }
}

window.updateTable = updateTable;
