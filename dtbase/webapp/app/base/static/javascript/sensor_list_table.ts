import { initialiseDataTable } from "./datatables";

function updateTable(sensors_for_each_type) {
  try {
    var selectedSensorType = document.getElementById("sensor_type").value;
    if (!selectedSensorType) {
      document.getElementById("sensorTable").innerHTML = "";
      return;
    }

    var sensors = sensors_for_each_type[selectedSensorType];
    var tableContent = "";

    // Construct the table headers
    tableContent += "<thead><tr><th class='num-column' scope='col'>#</th>"; // Adding '#' column
    for (var key in sensors[0]) {
      if (key !== "id") {
        // Exclude 'id' column
        tableContent += `<th scope='col'>${key}</th>`;
      }
    }
    tableContent += "</tr></thead>";

    // Construct the table body
    tableContent += "<tbody>";
    for (var i = 0; i < sensors.length; i++) {
      tableContent += "<tr><td class='num-column'>" + (i + 1) + "</td>"; // Adding row number
      for (var key in sensors[i]) {
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

window.updateTable = updateTable;
