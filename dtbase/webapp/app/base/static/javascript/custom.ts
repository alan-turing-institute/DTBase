/**
 * Resize function without multiple trigger
 *
 * Usage:
 * $(window).smartresize(function(){
 *     // code here
 * });
 */
(function ($, sr) {
  // debouncing function from John Hann
  // http://unscriptable.com/index.php/2009/03/20/debouncing-javascript-methods/
  const debounce = function (func, threshold, execAsap) {
    let timeout;

    return function debounced() {
      const obj = this;
      const args = arguments;
      function delayed() {
        if (!execAsap) func.apply(obj, args);
        timeout = null;
      }

      if (timeout) clearTimeout(timeout);
      else if (execAsap) func.apply(obj, args);

      timeout = setTimeout(delayed, threshold || 100);
    };
  };

  // smartresize
  jQuery.fn[sr] = function (fn) {
    return fn ? this.bind("resize", debounce(fn)) : this.trigger(sr);
  };
})(jQuery, "smartresize");
/**
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

const CURRENT_URL = window.location.href.split("#")[0].split("?")[0];
const $BODY = $("body");
const $MENU_TOGGLE = $("#menu_toggle");
const $SIDEBAR_MENU = $("#sidebar-menu");
const $SIDEBAR_FOOTER = $(".sidebar-footer");
const $LEFT_COL = $(".left_col");
const $RIGHT_COL = $(".right_col");
const $NAV_MENU = $(".nav_menu");
const $FOOTER = $("footer");

// Sidebar
function init_sidebar() {
  // TODO: This is some kind of easy fix, maybe we can improve this
  const setContentHeight = function () {
    // reset height
    $RIGHT_COL.css("min-height", $(window).height());

    const bodyHeight = $BODY.outerHeight();
    const footerHeight = $BODY.hasClass("footer_fixed")
      ? -10
      : $FOOTER.height();
    const leftColHeight = $LEFT_COL.eq(1).height() + $SIDEBAR_FOOTER.height();
    let contentHeight = bodyHeight < leftColHeight ? leftColHeight : bodyHeight;

    // normalize content
    contentHeight -= $NAV_MENU.height() + footerHeight;

    $RIGHT_COL.css("min-height", contentHeight);
  };

  $SIDEBAR_MENU.find("a").on("click", function (ev) {
    console.log("clicked - sidebar_menu");
    const $li = $(this).parent();

    if ($li.is(".active")) {
      $li.removeClass("active active-sm");
      $("ul:first", $li).slideUp(function () {
        setContentHeight();
      });
    } else {
      // prevent closing menu if we are on child menu
      if (!$li.parent().is(".child_menu")) {
        $SIDEBAR_MENU.find("li").removeClass("active active-sm");
        $SIDEBAR_MENU.find("li ul").slideUp();
      } else {
        if ($BODY.is(".nav-sm")) {
          $SIDEBAR_MENU.find("li").removeClass("active active-sm");
          $SIDEBAR_MENU.find("li ul").slideUp();
        }
      }
      $li.addClass("active");

      $("ul:first", $li).slideDown(function () {
        setContentHeight();
      });
    }
  });

  // toggle small or large menu
  $MENU_TOGGLE.on("click", function () {
    console.log("clicked - menu toggle");

    if ($BODY.hasClass("nav-md")) {
      $SIDEBAR_MENU.find("li.active ul").hide();
      $SIDEBAR_MENU
        .find("li.active")
        .addClass("active-sm")
        .removeClass("active");
    } else {
      $SIDEBAR_MENU.find("li.active-sm ul").show();
      $SIDEBAR_MENU
        .find("li.active-sm")
        .addClass("active")
        .removeClass("active-sm");
    }

    $BODY.toggleClass("nav-md nav-sm");

    setContentHeight();

    $(".dataTable").each(function () {
      $(this).dataTable().fnDraw();
    });
  });

  // check active menu
  $SIDEBAR_MENU
    .find('a[href="' + CURRENT_URL + '"]')
    .parent("li")
    .addClass("current-page");

  $SIDEBAR_MENU
    .find("a")
    .filter(function () {
      return this.href == CURRENT_URL;
    })
    .parent("li")
    .addClass("current-page")
    .parents("ul")
    .slideDown(function () {
      setContentHeight();
    })
    .parent()
    .addClass("active");

  // recompute content when resizing
  $(window).smartresize(function () {
    setContentHeight();
  });

  setContentHeight();
}

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
  init_sidebar();
  init_DataTables();
});
