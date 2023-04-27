document.addEventListener('DOMContentLoaded', function () {
    const addButton = document.querySelector('.btn-add-identifier');
    const identifierGroup = document.querySelector('.form-group:nth-of-type(3)');

    addButton.addEventListener('click', function () {
        const newRow = document.createElement('div');
        newRow.className = 'identifier-row';

        newRow.innerHTML = `
            <input type="text" class="form-control" name="identifier_name[]" placeholder="name, e.g. longitude" required>
            <input type="text" class="form-control" name="identifier_units[]" placeholder="units, e.g. degrees" required>
            <select class="form-control custom-select datatype-select" name="identifier_datatype[]" required>
                <option disabled selected value="">-- Select datatype --</option>
                <option value="string">string</option>
                <option value="float">float</option>
                <option value="integer">integer</option>
                <option value="boolean">boolean</option>
            </select>
            <button type="button" class="btn btn-danger btn-remove-identifier">-</button>
        `;

        newRow.querySelector('.btn-remove-identifier').addEventListener('click', function () {
            newRow.remove();
        });

        identifierGroup.appendChild(newRow);
    });
});
