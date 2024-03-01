from os import environ


class Config:
    # PostgreSQL database
    SQLALCHEMY_DATABASE_URI = "postgresql://{}:{}@{}:{}/{}".format(
        environ.get("DT_SQL_USER"),
        environ.get("DT_SQL_PASS"),
        environ.get("DT_SQL_HOST"),
        environ.get("DT_SQL_PORT"),
        environ.get("DT_SQL_DBNAME"),
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    # PostgreSQL database
    SQL_CONNECTION_STRING = "postgresql://{}:{}@{}:{}".format(
        environ.get("DT_SQL_USER"),
        environ.get("DT_SQL_PASS"),
        environ.get("DT_SQL_HOST"),
        environ.get("DT_SQL_PORT"),
    )
    SQL_DBNAME = environ.get("DT_SQL_DBNAME")


class TestConfig(Config):
    DEBUG = False
    DISABLE_REGISTER = True

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

    # Testing
    TESTING = True

    # PostgreSQL database
    SQL_CONNECTION_STRING = "postgresql://{}:{}@{}:{}".format(
        environ.get("DT_SQL_TESTUSER"),
        environ.get("DT_SQL_TESTPASS"),
        environ.get("DT_SQL_TESTHOST"),
        environ.get("DT_SQL_TESTPORT"),
    )
    SQL_DBNAME = environ.get("DT_SQL_TESTDBNAME")


class DebugConfig(Config):
    DEBUG = True
    DISABLE_REGISTER = True


config_dict = {"Production": ProductionConfig, "Test": TestConfig, "Debug": DebugConfig}
