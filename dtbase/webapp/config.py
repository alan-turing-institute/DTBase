import os


class Config:
    SECRET_KEY = os.environ.get("DT_FRONT_SECRET_KEY", None)
    # THEME SUPPORT
    #  if set then url_for('static', filename='', theme='')
    #  will add the theme name to the static URL:
    #    /static/<DEFAULT_THEME>/filename
    # DEFAULT_THEME = "themes/dark"
    DEFAULT_THEME = None


class ProductionConfig(Config):
    DEBUG = False
    DISABLE_REGISTER = True

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600


class TestConfig(Config):
    DEBUG = False
    DISABLE_REGISTER = True

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

    # Testing
    TESTING = True


class DebugConfig(Config):
    DEBUG = True
    DISABLE_REGISTER = True


class NoLoginConfig(DebugConfig):
    LOGIN_DISABLED = True


config_dict = {
    "Production": ProductionConfig,
    "Test": TestConfig,
    "Debug": DebugConfig,
    "No-login": NoLoginConfig,
}
