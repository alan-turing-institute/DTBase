import { SensorMeasure } from "./interfaces"

export function onPageLoad(existing_measures: SensorMeasure[]): void {
    const addButton = document.getElementById("addMeasureButton") as HTMLButtonElement
    const measureGroup = document.getElementById("formGroupMeasures") as HTMLDivElement
    const existingMeasureSelect = document.getElementById(
        "existingMeasureSelect",
    ) as HTMLSelectElement

    function createMeasureRow(measure: SensorMeasure | null = null) {
        const newRow = document.createElement("div")
        newRow.className = "measure-row"

        newRow.innerHTML = `
            <input type="hidden" name="measure_existing[]" value="${
                measure !== null ? "1" : "0"
            }">
            <input type="text" class="form-control" name="measure_name[]" placeholder="name, e.g. temperature" required value="${
                measure?.name || ""
            }" ${measure?.name ? "readonly" : ""}>
            <input type="text" class="form-control" name="measure_units[]" placeholder="units, e.g. degrees" required value="${
                measure?.units || ""
            }" ${measure?.units ? "readonly" : ""}>
            <select class="form-control custom-select datatype-select" name="${
                measure?.datatype ? "" : "measure_datatype[]"
            }" required ${measure?.datatype ? "readonly" : ""}>
            <option disabled ${
                !measure?.datatype ? "selected" : ""
            } value="">-- Select datatype --</option>
            ${["string", "float", "integer", "boolean"]
                .map(
                    (option) =>
                        `<option value="${option}" ${
                            measure?.datatype === option ? "selected" : ""
                        }>${option}</option>`,
                )
                .join("")}
            </select>
            ${
                measure?.datatype
                    ? `<input type="hidden" name="measure_datatype[]" value="${measure?.datatype}">`
                    : ""
            }
            <button type="button" class="btn btn-danger btn-remove-measure">-</button>
        `
        ;(
            newRow.querySelector(".btn-remove-measure") as HTMLButtonElement
        ).addEventListener("click", function () {
            newRow.remove()
        })

        measureGroup.appendChild(newRow)
    }

    addButton.addEventListener("click", function () {
        createMeasureRow()
    })

    existingMeasureSelect.addEventListener("change", function (event) {
        const target = event.target as HTMLSelectElement
        const selectedId = target.value

        if (selectedId) {
            const measure = existing_measures.find(
                (measure) => measure.id === parseInt(selectedId),
            )
            createMeasureRow(measure)
            target.value = ""
        }
    })
}

declare global {
    interface Window {
        onPageLoad: (existing_measures: SensorMeasure[]) => void
    }
}
window.onPageLoad = onPageLoad
