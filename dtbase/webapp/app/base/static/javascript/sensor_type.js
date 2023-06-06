document.addEventListener("DOMContentLoaded", function () {
  const addButton = document.querySelector(".btn-add-measure");
  const measureGroup = document.querySelector(".form-group:nth-of-type(3)");
  const existingMeasureSelect = document.querySelector(
    ".existing-measure-select"
  );

  function createMeasureRow(measure = {}) {
    const newRow = document.createElement("div");
    newRow.className = "measure-row";

    newRow.innerHTML = `
            <input type="hidden" name="measure_existing[]" value="${
              measure.is_existing ? "1" : "0"
            }">
            <input type="text" class="form-control" name="measure_name[]" placeholder="name, e.g. temperature" required value="${
              measure.name || ""
            }" ${measure.name ? "readonly" : ""}>
            <input type="text" class="form-control" name="measure_units[]" placeholder="units, e.g. degrees" required value="${
              measure.units || ""
            }" ${measure.units ? "readonly" : ""}>
            <select class="form-control custom-select datatype-select" name="${
              measure.datatype ? "" : "measure_datatype[]"
            }" required ${measure.datatype ? "readonly" : ""}>
            <option disabled ${
              !measure.datatype ? "selected" : ""
            } value="">-- Select datatype --</option>
            ${["string", "float", "integer", "boolean"]
              .map(
                (option) =>
                  `<option value="${option}" ${
                    measure.datatype === option ? "selected" : ""
                  }>${option}</option>`
              )
              .join("")}
            </select>
            ${
              measure.datatype
                ? `<input type="hidden" name="measure_datatype[]" value="${measure.datatype}">`
                : ""
            }
            <button type="button" class="btn btn-danger btn-remove-measure">-</button>
        `;

    newRow
      .querySelector(".btn-remove-measure")
      .addEventListener("click", function () {
        newRow.remove();
      });

    measureGroup.appendChild(newRow);
  }

  addButton.addEventListener("click", function () {
    createMeasureRow();
  });

  existingMeasureSelect.addEventListener("change", function () {
    const selectedId = this.value;

    if (selectedId) {
      const measure = existing_measures.find(
        (measure) => measure.id === parseInt(selectedId)
      );
      const selectedMeasure = { ...measure, is_existing: true }; // Create a new object
      createMeasureRow(selectedMeasure);
      this.value = "";
    }
  });
});
