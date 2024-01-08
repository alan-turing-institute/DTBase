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
    tableContent += "<th scope='col'></th>";
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
      tableContent += `<td>
      <button type="button" class="btn btn-warning btn-margin edit-button" data-sensor-id="${sensors[i]["id"]}"
          onclick="openEditModal(${sensors[i]["id"]}, '${selectedSensorType}')"> Edit  </button>
      </td> `;
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

//function openEditModal(sensorId, sensorType) {
//  // open a new window with the content of edit_form.html
//  console.log("sensorId: " + sensorId);
//  console.log("sensorType: " + sensorType);
//  var sensors = window.sensors_for_each_type[sensorType];
//  for (var key in sensors[0]) {
//    if (key !== "id") {
//      // Exclude 'id' column
//      console.log(key + ": " + sensors[0][key]);
//    }
//  }
//  var editWindow = window.open(
//    "/sensor_edit_form",//?id=" + sensorId +"&type=" + sensorType,
//    "_blank",
//    "width=600,height=400"
//  );
//}

function openEditModal(sensorId, sensorType) {
  //console.log("sensorId: " + sensorId);
  //console.log("sensorType: " + sensorType);

  // Use sensorType directly without 'selectedSensorType'
  var sensors = window.sensors_for_each_type[sensorType];

  // Find the selected sensor
  var selectedSensor = sensors.find((sensor) => sensor.id === sensorId);
  //console.log(sensors);
  //console.log(selectedSensor);

  // Check if the selected sensor is found
  if (selectedSensor) {
    // Clear previous content
    //var keysContainer = document.getElementById("sensorKeysContainer");
    //if (keysContainer) {
    //  keysContainer.innerHTML = "";

    // Display keys for the selected sensor
    //for (var key in selectedSensor) {
    //  if (key !== "id") {
    //    console.log(key + ": " + selectedSensor[key]);

    //    // Display keys in the popup window
    //    var keyElement = document.createElement("p");
    //    keyElement.textContent = key;
    //    //keysContainer.appendChild(keyElement);
    //  }
    //}

    // Open the popup window after displaying keys
    var editWindow = window.open(
      "/sensor_edit_form?id=" + sensorId + "&type=" + sensorType,
      "_blank",
      "width=600,height=400"
    );

    //} else {
    //  console.error("Keys container not found");
    //}
  } else {
    console.error("Selected sensor not found");
  }
}
