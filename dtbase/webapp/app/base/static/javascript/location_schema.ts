import { LocationIdentifier } from "./interfaces";

export function onPageLoad(existing_identifiers: LocationIdentifier[]): void {
  const addButton = document.getElementById(
    "addIdentifierButton"
  ) as HTMLButtonElement;
  const identifierGroup = document.getElementById(
    "identifiersFormGroup"
  ) as HTMLDivElement;
  const existingIdentifierSelect = document.getElementById(
    "existingIdentifierSelect"
  ) as HTMLSelectElement;

  addButton.addEventListener("click", function () {
    createIdentifierRow(identifierGroup);
  });

  existingIdentifierSelect.addEventListener("change", function (event) {
    const target = event.target as HTMLSelectElement;
    const selectedId = target.value;

    if (selectedId) {
      const identifier = existing_identifiers.find(
        (identifier) => identifier.id === parseInt(selectedId)
      );
      createIdentifierRow(identifierGroup, identifier);
      target.value = "";
    }
  });
}
function createIdentifierRow(
  identifierGroup: HTMLDivElement,
  identifier: null | LocationIdentifier = null
): void {
  const newRow = document.createElement("div");
  newRow.className = "identifier-row";

  newRow.innerHTML = `
    <input type="hidden" name="identifier_existing[]" value="${
      identifier !== null ? "1" : "0"
    }">
    <input type="text" class="form-control" name="identifier_name[]" placeholder="name, e.g. longitude" required value="${
      identifier?.name || ""
    }" ${identifier?.name ? "readonly" : ""}>
    <input type="text" class="form-control" name="identifier_units[]" placeholder="units, e.g. degrees" required value="${
      identifier?.units || ""
    }" ${identifier?.units ? "readonly" : ""}>
    <select class="form-control custom-select datatype-select" name="${
      identifier?.datatype ? "" : "identifier_datatype[]"
    }" required ${identifier?.datatype ? "readonly" : ""}>
    <option disabled ${
      !identifier?.datatype ? "selected" : ""
    } value="">-- Select datatype --</option>
    ${["string", "float", "integer", "boolean"]
      .map(
        (option) =>
          `<option value="${option}" ${
            identifier?.datatype === option ? "selected" : ""
          }>${option}</option>`
      )
      .join("")}
        </select>
        ${
          identifier?.datatype
            ? `<input type="hidden" name="identifier_datatype[]" value="${identifier?.datatype}">`
            : ""
        }
        <button type="button" class="btn btn-danger btn-remove-identifier">-</button>
        `;

  (
    newRow.querySelector(".btn-remove-identifier") as HTMLButtonElement
  ).addEventListener("click", function () {
    newRow.remove();
  });

  identifierGroup.appendChild(newRow);
}

declare global {
  interface Window {
    onPageLoad: (existing_identifiers: LocationIdentifier[]) => void;
  }
}

window.onPageLoad = onPageLoad;
