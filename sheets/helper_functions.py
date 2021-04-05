from decimal import Decimal, DecimalException
from .errors import CellError, CellErrorType
from .cell import get_cell_tuple, get_cell_name


def is_error(val, error_type):
    '''helper to check if error'''
    if isinstance(val, CellError):
        if val.get_type() == error_type:
            return True
    return False

# helper function for string conversions
def convert_to_string(a):
    '''converts to string for necessary functions'''
    if type(a) == str:
        return a
    else:
        if type(a) == bool:
            if a:
                return "TRUE"
            else:
                return "FALSE"

        elif type(a) == Decimal:
            return str(a)

        elif a is None:
            return ""

        else:
            raise ValueError("{} cannot be converted to string".format(a))

def get_empty_bool(val):
    ''' Given val as the non empty operand, returns the bool for the
        empty cell of that type. '''
    if type(val) == str:
        return ""
    if type(val) == Decimal:
        return Decimal(0)
    if type(val) == bool:
        return False

def compute_bool(a, b, op):
    ''' Computes the boolean operation given operator string and operands.'''
    if op in ["==", "="]:
        return a == b
    elif op in ["<>", "!="]:
        return a != b
    elif op == "<=":
        return a <= b
    elif op == "<":
        return a < b
    elif op == ">=":
        return a >= b
    elif op == ">":
        return a > b
    else:
        pass

def compare(b1, b2, op):
    '''Computes the boolean result for compare'''
    # check if none
    if b1 is None and b2 is not None:
        b1 = get_empty_bool(b2)
    if b2 is None and b1 is not None:
        b2 = get_empty_bool(b1)
    if b1 is None and b2 is None:
        b1 = 0
        b2 = 0

    val = True

    # Both operands are same type
    if type(b1) == type(b2):
        if type(b1) == str: # Strings are compared in lowercase
            b1, b2 = b1.lower(), b2.lower()
        val = compute_bool(b1, b2, op)

    elif type(b1) == bool and (type(b2) == str or type(b2) == Decimal):
        val = False
        if op in [">=", ">", "!=", "<>"]: #Booleans greater than strings/numbers
            val = True

    elif type(b2) == bool and (type(b1) == str or type(b1) == Decimal):
        val = False
        if op in ["<=", "<", "!=", "<>"]: #Booleans greater than strings/numbers
            val = True

    elif type(b1) == str and type(b2) == Decimal:
        val = False
        if op in [">=", ">", "!=", "<>"]: #Strings greater than numbers
            val = True

    elif type(b2) == str and type(b1) == Decimal:
        val = False
        if op in ["<=", "<", "!=", "<>"]: #Strings greater than numbers
            val = True

    else:
        print("uh oh")
        val = True
    return val
