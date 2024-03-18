# DTBase Frontend

The DTBase frontend is a web server, implemented using Flask, that serves a graphical user interface for the digital twin.

Anything the frontend can achieve in manipulating the twin it does by calling various backend endpoints. It is essentially a graphical interface for the backend with some basic plotting.

The user interfaces of digital twins tend to be largely bespoke. Hence the DTBase frontend is quite basic, and we expect the user to develop it further to serve their own needs, by for instance implementing data dashboards and visualisations that serve their needs. In developing DTBase, our philosophy has been to lead with the backend, and consider frontend features largely nice-to-have addons. Hence some parts of the frontend lag behind the backend in capabilities, and there are things you can currently do only through the backend.

The frontend is a mixture of Python (Flask), Typescript, CSS, and Jinja HTML templates. In this it differs from the rest of the codebase, which is pure Python. Consequently at the root of `dtbase/frontend` are configuration files for `webpack`, `eslint`, and `prettier`, plus a `package.json` that specifies our Typescript dependencies.

Some notable Typescript dependencies are
* Bootstrap 5 for a grid layout of the pages.
* Datatables for styling our many tables.
* Chart.js for plotting.

## Code structure
* `run.sh`. This is the shell script that starts the web server. It does two things of note:
    * Runs the Typescript compiler, producing Javascript that can be included in the pages sent to the browser, using webpack.
    * Runs the Flask app.
  If the environment variable `FLASK_DEBUG` is set to `1` both of these are run in "watch mode", where they watch for updates to local files and recompile/restart as necessary. This is handy when developing.
* `frontend_app.py`. A simple script that calls `create_app` from `app/__init__.py`.
* `app/__init__.py`. Module for setting up the Flask app with all its settings and such.
* `app/home`, `/locations/`, `/models`, `/sensors`, etc. Each of these has the code for the pages in that subsection for the site. They all have a `routes.py` that defines the Flask routes, and a `templates` folder for the Jinja templates.
* `app/base`. Various resources shared by the different sections of the site. Most notably
    * `templates`. All the base Jinja templates for things like the sidebar, the login page, and error pages.
    * `static`. All the CSS and Typescript. See [dtbase/frontend/app/base/static/README.md](app/base/static/README.md) for more details.
    * `static/node_modules`. A symbolic link from `dtbase/frontend/node_modules`. This way all the Typescript dependencies are under the `static` folder and thus easy to load and import from.
* `exc.py`. Custom exception types used by the frontend.
* `config.py`. Configuration options like debug mode and dev mode for the frontend.
* `user.py`. Everything related authentication on the frontend. We use the `flask-login` plugin to handle logins. Logging in simply means getting a JWT token from the backend, and a user is logged in as long as there's a valid JWT token associated with their session.
* `utils.py`. Miscellaneous Python utilities.

## Our Approach to Typescript and Javascript

The vast majority of client-side code is written in Typescript, and it should be in the `/app/base/static/typescript` (henceforth just `typescript`) folder as `.ts` files. Webpack, which gets run by `run.sh` when starting the frontend webserver, sorts out dependencies and transpiles the Typescript into `.js` files in the `/app/base/static/javascript` folder. There will be one `.js` file for every `.ts` file. The Jinja HTML templates can then include these transpiled Javascript files using `<script>` tags.

The only pure, non-typed Javascript one should ever write should be minimal amounts in `<script>` tags in the Jinja templates. The reason we do this at all is that Flask passes some data to the Jinja templates which needs to be further be passed onto functions we've written in Typescript. The typical usage pattern looks something like this. In the HTML template we have

```jinja-html
{% block javascripts %}
{{ super() }}
<script src="{{ url_for('static', filename='javascript/sensor_list_table.js') }}"></script>
<script>
  const sensors_for_each_type = {{ sensors_for_each_type | tojson | safe }};
  window.addEventListener("DOMContentLoaded", (event) => {
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

export function updateTable(sensors_for_each_type) {
  // blahblah, bunch of things happen here
}

window.updateTable = updateTable;
```

It imports from another module we've written using the ES6 import syntax and defines `updateTable`. It then effectively "exports" this function to be visible in the global scope, and thus usable in the above snippet in the Jinja template, by assigning it to `window.updateTable`. (It also exports it in the ES6 exports sense, so that other Typescript modules can use it.)

When reading the `.ts` files, anything assigned to a field of `window` is to be used in the templates. All imports/exports between the typescript files should use the ES6 syntax. The Typescript files should not ever assume the presence of any global variables.
