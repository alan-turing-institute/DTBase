import DataTable from "datatables.net-bs5";
import "datatables.net-buttons-bs5";
import "datatables.net-buttons/js/buttons.html5";
import "datatables.net-fixedheader-bs5";
import "datatables.net-responsive-bs5";

export function initialiseDataTable(selector) {
  const table = new DataTable(selector, {
    buttons: ["copy", "csv"],
    fixedHeader: true,
    responsive: true,
  });
  table.buttons().container().appendTo(table.table().container());
}

window.initialiseDataTable = initialiseDataTable;
