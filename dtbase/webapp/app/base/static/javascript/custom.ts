/* DATA TABLES */

function init_DataTables() {
  if (typeof $.fn.DataTable === "undefined") {
    return;
  }

  const handleDataTableButtons = function () {
    if ($("#datatable-buttons").length) {
      $("#datatable-buttons").DataTable({
        dom: "Bfrtip",
        buttons: [
          {
            extend: "copy",
            className: "btn-sm",
          },
          {
            extend: "csv",
            className: "btn-sm",
          },
          {
            extend: "excel",
            className: "btn-sm",
          },
          {
            extend: "pdfHtml5",
            className: "btn-sm",
          },
          {
            extend: "print",
            className: "btn-sm",
          },
        ],
        responsive: true,
      });
    }
  };

  TableManageButtons = (function () {
    "use strict";
    return {
      init: function () {
        handleDataTableButtons();
      },
    };
  })();

  $("#datatable").dataTable();

  $("#datatable-keytable").DataTable({
    keys: true,
  });

  $("#datatable-responsive").DataTable();

  $("#datatable-scroller").DataTable({
    ajax: "js/datatables/json/scroller-demo.json",
    deferRender: true,
    scrollY: 380,
    scrollCollapse: true,
    scroller: true,
  });

  $("#datatable-fixed-header").DataTable({
    fixedHeader: true,
  });

  const $datatable = $("#datatable-checkbox");

  $datatable.dataTable({
    order: [[1, "asc"]],
    columnDefs: [{ orderable: false, targets: [0] }],
  });

  TableManageButtons.init();
}

$(document).ready(function () {
  init_DataTables();
});
