from os import environ


class Config(object):
    SECRET_KEY = "V96fj5eJf9ukM4U+xG3IapXqETjNFjV/kNy4PqpZUCE0bxy7Cyr8LKWMrKIO2Sw"
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
