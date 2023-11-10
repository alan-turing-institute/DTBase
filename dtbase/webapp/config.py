import os


class Config(object):
    try:
        SECRET_KEY = os.environ["DT_FRONT_SECRET_KEY"]
    except KeyError:
        raise RuntimeError("Environment variable DT_FRONT_SECRET_KEY must be set.")
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


config_dict = {"Production": ProductionConfig, "Test": TestConfig, "Debug": DebugConfig}
