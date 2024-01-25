import { LocationSchema } from "./interfaces";

export function updateForm(schemas: LocationSchema[]): void {
  const schemaId = (document.getElementById("schema") as HTMLSelectElement)
    .value;
  const identifiersDiv = document.getElementById(
    "identifiers"
  ) as HTMLDivElement;
  identifiersDiv.innerHTML = "";

  // find the selected schema
  const selectedSchema = schemas.find((schema) => schema.name == schemaId);

  // If there's no selected schema or it has no identifiers, then return.
  if (!selectedSchema || !selectedSchema.identifiers) return;

  // Add form fields for each identifier
  for (const identifier of selectedSchema.identifiers) {
    const identifierDiv = document.createElement("div");
    identifierDiv.className = "form-group";
    identifierDiv.innerHTML = `
            <label>${identifier.name} (${identifier.units}, ${identifier.datatype})</label>
            <input type="text" class="form-control custom-input" id="${identifier.name}" name="identifier_${identifier.name}" placeholder="Value" required>
        `;
    identifiersDiv.appendChild(identifierDiv);
  }
}

declare global {
  interface Window {
    updateForm: (selector: LocationSchema[]) => void;
  }
}
window.updateForm = updateForm;
