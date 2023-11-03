function updateForm() {
  const schemaId = document.getElementById("schema").value;
  const identifiersDiv = document.getElementById("identifiers");
  identifiersDiv.innerHTML = "";

  // find the selected schema
  const selectedSchema = window.schemas.find(
    (schema) => schema.name == schemaId
  );

  // If there's no selected schema or it has no identifiers, then return.
  if (!selectedSchema || !selectedSchema.identifiers) return;

  // Add form fields for each identifier
  for (let identifier of selectedSchema.identifiers) {
    let identifierDiv = document.createElement("div");
    identifierDiv.className = "form-group";
    identifierDiv.innerHTML = `
            <label>${identifier.name} (${identifier.unit}, ${identifier.datatype})</label>
            <input type="text" class="form-control custom-input" id="${identifier.name}" name="identifier_${identifier.name}" placeholder="Value" required>
        `;
    identifiersDiv.appendChild(identifierDiv);
  }
}

window.onload = function () {
  document.getElementById("schema").addEventListener("change", updateForm);
};
