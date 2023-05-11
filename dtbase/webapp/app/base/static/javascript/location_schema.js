document.addEventListener('DOMContentLoaded', function () {
    const addButton = document.querySelector('.btn-add-identifier');
    const identifierGroup = document.querySelector('.form-group:nth-of-type(3)');
    const existingIdentifierSelect = document.querySelector('.existing-identifier-select');

    function createIdentifierRow(identifier = {}) {
        const newRow = document.createElement('div');
        // newRow.className = 'identifier-row row';
        newRow.className = 'identifier-row';

        newRow.innerHTML = `
            <input type="text" class="form-control" name="identifier_name[]" placeholder="name, e.g. longitude" required value="${identifier.name || ''}" ${identifier.name ? 'readonly' : ''}>
            <input type="text" class="form-control" name="identifier_units[]" placeholder="units, e.g. degrees" required value="${identifier.units || ''}" ${identifier.units ? 'readonly' : ''}>
            <select class="form-control custom-select datatype-select" name="identifier_datatype[]" required ${identifier.datatype ? 'disabled' : ''}>
                <option disabled ${!identifier.datatype ? 'selected' : ''} value="">-- Select datatype --</option>
                ${['string', 'float', 'integer', 'boolean'].map(option => `<option value="${option}" ${identifier.datatype === option ? 'selected' : ''}>${option}</option>`).join('')}
            </select>
            <button type="button" class="btn btn-danger btn-remove-identifier">-</button>
        `;

        newRow.querySelector('.btn-remove-identifier').addEventListener('click', function () {
            newRow.remove();
        });

        identifierGroup.appendChild(newRow);
    }

    addButton.addEventListener('click', function () {
        createIdentifierRow();
    });

    existingIdentifierSelect.addEventListener('change', function () {
        const selectedId = this.value;

        if (selectedId) {
            const selectedIdentifier = existing_identifiers.find(identifier => identifier.id === parseInt(selectedId));
            createIdentifierRow(selectedIdentifier);
            this.value = '';
        }
    });
});
