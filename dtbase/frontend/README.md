# DTBase Frontend

The DTBase frontend is a web server, implemented using Flask, that serves a graphical user interface for the digital twin.

Anything the frontend can achieve in manipulating the twin it does by calling various backend endpoints. It is essentially a graphical interface for the backend with some basic plotting.

The user interfaces of digital twins tend to be quite bespoke. Hence the DTBase frontend is quite basic, and we expect the user to develop it further to serve their own needs, by for instance implementing data dashboards and visualisations that serve their needs. In developing DTBase, our philosophy has been to lead with the backend, and consider frontend features to be nice-to-have addons. Hence some parts of the frontend lag behind the backend in capabilities, and there are things you can't currently do using just the frontend.

The frontend is a mixture of Python (Flask), Typescript, CSS, and Jinja HTML templates. In this it differs from the rest of the codebase, which is pure Python. Consequently at the root of `dtbase/frontend` are configuration files for `webpack`, `eslint`, and `prettier`, plus a `package.json` that specifies our Typescript dependencies.

Some notable Typescript dependencies are
* Bootstrap 5 for a grid layout of the pages.
* Datatables for styling our many tables.
* Chart.js for plotting.

## Code structure
* `run.sh`. This is the shell script that starts the web server. It does two things of note:
    * Runs the Typescript compiler, producing Javascript that can be included in the pages sent to the browser, using webpack.
    * Runs the Flask app.
  If the environment variable `FLASK_DEBUG` is set to `1` both of these are run in "watch mode", where they watch for updates to local files and recompile/restart as necessary, usefully for development.
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
