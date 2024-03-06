from flask import Blueprint

blueprint = Blueprint(
    "services_blueprint",
    __name__,
    url_prefix="/services",
    template_folder="templates",
    static_folder="static",
)
