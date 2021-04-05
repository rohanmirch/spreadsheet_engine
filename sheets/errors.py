''' This file specifies the API that we expect your implementation to conform to.
# You will likely want to move these classes into various files, but the tests
# will expect these to be available when the "sheets" module is imported.

# If you are unfamiliar with Python 3 type annotations, see the Python standard
# library documentation for the typing module here:
#
#     https://docs.python.org/3/library/typing.html '''
import enum
from typing import Optional

class CellErrorType(enum.Enum):
    '''
    This enum specifies the kinds of errors that spreadsheet cells can hold.
    '''

    # A formula doesn't parse successfully
    PARSE_ERROR = 1

    # Unrecognized name
    BAD_NAME = 2

    # A value of the wrong type was encountered during evaluation
    TYPE_ERROR = 3

    # A cell is part of a circular reference
    CIRCULAR_REFERENCE = 4

    # A divide-by-zero was encountered during evaluation
    DIVIDE_BY_ZERO = 5


class CellError(): ### added the Exception
    '''
    This class represents an error result from cell parsing or evaluation.
    '''

    def __init__(self, error_type: CellErrorType, detail: str,
                 exception: Optional[Exception] = None):
        self._error_type = error_type
        self._detail = detail
        self._exception = exception

    def get_type(self) -> CellErrorType:
        ''' The category of the cell error. '''
        return self._error_type

    def get_detail(self) -> str:
        ''' More detail about the cell error. '''
        return self._detail

    def get_exception(self) -> Optional[Exception]:
        '''
        If the cell error was generated from a raised exception, this is the
        exception that was raised.  Otherwise this will be None.
        '''
        return self._exception

    def __str__(self) -> str:
        return f'{self._error_type}:  {self._detail}'
