from flask import Blueprint

blueprint = Blueprint(
    "models_blueprint",
    __name__,
    url_prefix="/models",
    template_folder="templates",
    static_folder="static",
)
