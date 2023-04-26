document.addEventListener('DOMContentLoaded', function() {
    const addButton = document.querySelector('.btn-add-identifier');
    const identifierGroup = document.querySelector('.form-group:nth-of-type(2)');

    addButton.addEventListener('click', function() {
        const newRow = document.createElement('div');
        newRow.className = 'identifier-row';

        newRow.innerHTML = `
            <input type="text" class="form-control" name="identifier_name[]" placeholder="Name" required>
            <input type="text" class="form-control" name="identifier_units[]" placeholder="Units" required>
            <input type="text" class="form-control" name="identifier_datatype[]" placeholder="Datatype" required>
            <button type="button" class="btn btn-danger btn-remove-identifier">-</button>
        `;

        newRow.querySelector('.btn-remove-identifier').addEventListener('click', function() {
            newRow.remove();
        });

        identifierGroup.appendChild(newRow);
    });
});