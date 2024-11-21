from contextlib import contextmanager


class MissingExpectedError(Exception):
    pass


@contextmanager
def raises(err_type, /, *, msg=None):
    """Check that a code block raises the expected error

    err_type:
        The exception class to check for
    msg: str
        If given, must appear as a substring of the error msg

    Example:

        >>> arr = [1, 2, 3]
        >>> with raises(IndexError):
        ...     arr[5]

    """
    try:
        yield
    except err_type as err:
        if msg and msg not in str(err):
            raise MissingExpectedError(
                f"Expected error {err_type} occurred but does not contain the expected message:"
                f"\n\tEXPECTED: {msg}"
                f"\n\tGOT     : {str(err)}"
            )
    else:
        raise MissingExpectedError(f"Expected error {err_type} not raised")
