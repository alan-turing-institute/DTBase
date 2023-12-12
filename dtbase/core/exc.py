class RowExistsError(Exception):
    pass


class RowMissingError(Exception):
    pass


class TooManyRowsError(Exception):
    pass


class DatabaseConnectionError(Exception):
    pass
