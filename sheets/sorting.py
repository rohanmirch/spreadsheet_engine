''' Helper file to implement sorting proxy '''
from .errors import CellError, CellErrorType
from decimal import Decimal
from functools import total_ordering

@total_ordering
class rowProxy:
    ''' Proxy object for sorting rows '''
    def __init__(self, row_ind, sort_cols, row_vals):
        self.row_vals = row_vals
        self.row_ind = row_ind
        self.sort_cols = sort_cols

    def __lt__(self, other):
        ''' Returns true if current object is less than other'''
        for index in self.sort_cols:
            if index > 0:
                v1 = self.row_vals[index - 1]
                v2 = other.row_vals[index - 1]
            else:
                v2 = self.row_vals[(-index) - 1]
                v1 = other.row_vals[(-index) - 1]

            if less_than(v1, v2):
                return True
            elif equals(v1, v2):
                continue
            else:
                return False

        # We reach end of row, all equal
        return False

    def __eq__(self, other):
        for index in self.sort_cols:
            index = abs(index)
            v1 = self.row_vals[index - 1]
            v2 = other.row_vals[index - 1]
            if not equals(v1, v2):
                return False
        # We reach end of row, all equal
        return True

def less_than(b1, b2):
    '''Computes the boolean result for compare'''
    # None <  Error < decimal < string <  bool

    # Check for None first
    if b1 is None and b2 is not None:
        return True
    if b1 is not None and b2 is None:
        return False
    if b1 is None and b2 is None:
        return False

    # Check for CellError
    if isinstance(b1, CellError) and not isinstance(b2, CellError):
        return True
    if not isinstance(b1, CellError) and isinstance(b2, CellError):
        return False
    if isinstance(b1, CellError) and isinstance(b2, CellError):
        return b1.get_type().value < b2.get_type().value


    # Both operands are same type
    if type(b1) == type(b2):
        if type(b1) == str: # Strings are compared in lowercase
            b1, b2 = b1.lower(), b2.lower()
        return b1 < b2

    # bool > (strings, decimals)
    elif type(b1) == bool and (type(b2) == str or type(b2) == Decimal):
        return False

    elif type(b2) == bool and (type(b1) == str or type(b1) == Decimal):
        return True

    # String < decimals
    elif type(b1) == str and type(b2) == Decimal:
        return False
    elif type(b2) == str and type(b1) == Decimal:
        return True
    else:
        print("uh oh")
        return True

def equals(b1, b2):
    ''' Tests if two objects are equal'''
    if isinstance(b1, CellError) and isinstance(b2, CellError):
        return b1.get_type().value == b2.get_type().value

    return b1 == b2
