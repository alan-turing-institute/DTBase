import { initialiseDataTable } from "./datatables";
import { Location } from "./interfaces";

export function updateLocationsTable(locations_for_each_schema: {
  [key: string]: Location[];
}): void {
  try {
    const selectedSchema = (
      document.getElementById("schema") as HTMLSelectElement
    ).value;
    if (!selectedSchema) {
      document.getElementById("locationTableWrapper").innerHTML = "";
      return;
    }

    const locations = locations_for_each_schema[selectedSchema];
    let tableContent = "";

    // Construct the table headers
    tableContent += "<thead><tr><th class='num-column' scope='col'>#</th>"; // Adding '#' column
    for (const key in locations[0]) {
      if (key !== "id") {
        // Exclude 'id' column
        tableContent += `<th scope='col'>${key}</th>`;
      }
    }
    tableContent += "</tr></thead>";

    // Construct the table body
    tableContent += "<tbody>";
    for (let i = 0; i < locations.length; i++) {
      tableContent += "<tr><td class='num-column'>" + (i + 1) + "</td>"; // Adding row number
      for (const key in locations[i]) {
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

declare global {
  interface Window {
    updateLocationsTable: (locations_for_each_schema: {
      [key: string]: Location[];
    }) => void;
  }
}

window.updateLocationsTable = updateLocationsTable;
