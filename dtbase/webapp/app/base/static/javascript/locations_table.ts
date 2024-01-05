import { initialiseDataTable } from "./datatables";

function updateTable(locations_for_each_schema) {
  try {
    var selectedSchema = document.getElementById("schema").value;
    if (!selectedSchema) {
      document.getElementById("locationTableWrapper").innerHTML = "";
      return;
    }

    var locations = locations_for_each_schema[selectedSchema];
    var tableContent = "";

    // Construct the table headers
    tableContent += "<thead><tr><th class='num-column' scope='col'>#</th>"; // Adding '#' column
    for (var key in locations[0]) {
      if (key !== "id") {
        // Exclude 'id' column
        tableContent += `<th scope='col'>${key}</th>`;
      }
    }
    tableContent += "</tr></thead>";

    // Construct the table body
    tableContent += "<tbody>";
    for (var i = 0; i < locations.length; i++) {
      tableContent += "<tr><td class='num-column'>" + (i + 1) + "</td>"; // Adding row number
      for (var key in locations[i]) {
        if (key !== "id") {
          // Exclude 'id' column
          tableContent += `<td>${locations[i][key]}</td>`;
        }
      }
      tableContent += "</tr>";
    }
    tableContent += "</tbody>";

    // Construct the full table and inject it into the DOM
    const fullTable = `<table id="datatable" class="table table-striped table-hover nowrap" style="width:100%">${tableContent}</table>`;

    document.getElementById("locationTableWrapper").innerHTML = fullTable;
    initialiseDataTable("#datatable");
  } catch (error) {
    console.error(error);
  }
}

window.updateTable = updateTable;
