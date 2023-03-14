from dtbase.core.structure import SQLA as db


def add_default_session(func):
    """Decorator for adding a default value of db.session for the `session` argument."""

    def new_func(*args, session=None, **kwargs):
        if session is None:
            session = db.session
        return func(*args, session=session, **kwargs)

    return new_func
