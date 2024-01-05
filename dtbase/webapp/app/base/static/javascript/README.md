This README describes how DTBase uses Typescript and Javascript.

The vast majority of client-side code should be written in Typescript, and it should be in this folder as `.ts` files. Webpack, which gets run by `run.sh` when starting the frontend webserver, sorts out dependencies and transpiles the Typescript into `.js` files in this same folder. There will be one `.js` file for every `.ts` file. The Jinja HTML templates can then include these transpiled Javascript files using `<script>` tags.

The only pure, non-typed Javascript one should ever write should be minimal amounts in `<script>` tags in the Jinja templates. The reason we do this at all is that Flask passes some data to the Jinja templates which needs to be further be passed onto functions we've written in Typescript.

The typical usage pattern looks something like this. In the HTML template we have

```jinja-html
{% block javascripts %}
{{ super() }}
<script src="{{ url_for('static', filename='javascript/sensor_list_table.js') }}"></script>
<script>
  const sensors_for_each_type = {{ sensors_for_each_type | tojson | safe }};
  window.addEventListener("DOMContentLoaded", (event) => {
    const sensorTypeSelector = document.getElementById("sensor_type");
    sensorTypeSelector.addEventListener(
      "change", () => window.updateTable(sensors_for_each_type)
    );
    window.updateTable(sensors_for_each_type);
  });
</script>
{% endblock javascripts %}
```

The first `<script>` tag includes a file transpiled from `sensor_list_table.ts`. The second `<script>` tag includes a small snippet that

1. Reads the data passed to us by Flask into a variable `sensors_for_each_type`.
2. On page load calls the function `window.updateTable` defined in `sensor_list_table.ts` with `sensors_for_each_type`.

`sensor_list_table.ts` looks like this:

```typescript
import { initialiseDataTable } from "./datatables";

function updateTable(sensors_for_each_type) {
  // blahblah, bunch of things happen here
}

window.updateTable = updateTable;
```

It imports from another module we've written using the ES6 import syntax and defines `updateTable`. It then effectively "exports" this function to be visible in the global scope, and thus usable in the above snippet in the Jinja template, by assigning it to `window.updateTable`.

When reading the `.ts` files, anything assigned to a field of `window` is to be used in the templates. All imports/exports between the typescript files should use the ES6 syntax. The Typescript files should not ever assume the presence of any global variables.
