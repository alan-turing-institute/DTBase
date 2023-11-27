window.addEventListener("DOMContentLoaded", (event) => {
  var sensorTypeSelector = document.getElementById("sensor_type");
  sensorTypeSelector.addEventListener("change", updateTable);
  updateTable();
});

function updateTable() {
  try {
    var selectedSensorType = document.getElementById("sensor_type").value;
    if (!selectedSensorType) {
      document.getElementById("sensorTable").innerHTML = "";
      return;
    }

    var sensors = window.sensors_for_each_type[selectedSensorType];
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
      tableContent += `<td><button type='button' class='btn btn-danger btn-margin' onclick='confirmDeleteSensor(${sensors[i].id})'>Delete</button></td>`;
      tableContent += `<td><button type='button' class='btn btn-warning btn-margin' onclick='editSensor(${sensors[i].id})'>Edit</button></td>`;
      tableContent += "</tr>";
    }
    tableContent += "</tbody>";

    // Construct the full table and inject it into the DOM
    var fullTable = `<div class='table-responsive'><table class='table sensor-table table-striped table-hover'>${tableContent}</table></div>`;
    document.getElementById("sensorTable").innerHTML = fullTable;

    // Get the number of columns
    var numOfColumns = Object.keys(sensors[0]).length;

    // Calculate table width based on number of columns.
    var tableWidth = 120 * numOfColumns;

    // Set a maximum table width if required
    tableWidth = Math.min(tableWidth, 1000);

    var tableElement = document.querySelector(".sensor-table");
    tableElement.style.width = tableWidth + "px";
  } catch (error) {
    console.error(error);
  }
}

function confirmDeleteSensor(sensorId) {
  var confirmation = window.confirm(
    "Are you sure you want to delete this sensor?"
  );
  if (confirmation) {
    // User clicked "OK" in the confirmation popup
    deleteSensor(sensorId);
  } else {
    // User clicked "Cancel" in the confirmation popup
    // You can add additional logic if needed
  }
}

function editSensor(sensorId) {
  // Your logic to handle the form submission for the specific sensor
  alert("Editing sensor ID: " + sensorId);
}
