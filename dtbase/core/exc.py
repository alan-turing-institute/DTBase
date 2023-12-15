class RowExistsError(Exception):
    pass


class RowMissingError(Exception):
    pass


class TooManyRowsError(Exception):
    pass


class DatabaseConnectionError(Exception):
    pass


class BackendCallError(Exception):
    """An error to be raised when an API request for the backend does not return the
    expected, successful result."""

    pass
