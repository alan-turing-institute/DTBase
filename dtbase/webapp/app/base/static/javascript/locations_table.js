window.addEventListener('DOMContentLoaded', (event) => {
    var schemaSelector = document.getElementById('schema');
    schemaSelector.addEventListener('change', updateTable);
    updateTable();
});

function updateTable() {
    try {
        var selectedSchema = document.getElementById('schema').value;
        if (!selectedSchema) {
            document.getElementById("locationTable").innerHTML = "";
            return;
        }

        var locations = window.locations_for_each_schema[selectedSchema];
        var tableContent = '';
        
        // Construct the table headers
        tableContent += "<thead><tr><th class='num-column' scope='col'>#</th>"; // Adding '#' column
        for (var key in locations[0]) {
            if (key !== 'id') { // Exclude 'id' column
                tableContent += `<th scope='col'>${key}</th>`;
            }
        }
        tableContent += "</tr></thead>";
        
        // Construct the table body
        tableContent += "<tbody>";
        for (var i = 0; i < locations.length; i++) {
            tableContent += "<tr><td class='num-column'>" + (i + 1) + "</td>"; // Adding row number
            for (var key in locations[i]) {
                if (key !== 'id') { // Exclude 'id' column
                    tableContent += `<td>${locations[i][key]}</td>`;
                }
            }
            tableContent += "</tr>";
        }
        tableContent += "</tbody>";

        // Construct the full table and inject it into the DOM
        var fullTable = `<div class='table-responsive'><table class='table location-table table-striped table-hover'>${tableContent}</table></div>`;
        document.getElementById("locationTable").innerHTML = fullTable;

        // Get the number of columns
        var numOfColumns = Object.keys(locations[0]).length;

        // Calculate table width based on number of columns. 
        var tableWidth = 120 * numOfColumns; 

        // Set a maximum table width if required
        tableWidth = Math.min(tableWidth, 1000); 

        var tableElement = document.querySelector('.location-table');
        tableElement.style.width = tableWidth + "px";
    } catch (error) {
        console.error(error);
    }
}
