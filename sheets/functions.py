'''Functions to be used in sheets'''
from functools import reduce
from decimal import Decimal
from .errors import CellError, CellErrorType
from .helper_functions import compare, is_error
import sheets


# helper function for boolean conversions
def convert_to_bool(args):
    '''convert types to bool for functions'''
    new = []
    for a in args:
        if type(a) == bool:
            new.append(a)
        else:
            if type(a) == str:
                if a.lower() == "true":
                    new.append(True)
                elif a.lower() == "false":
                    new.append(False)
                else:
                    raise ValueError("{} cannot be converted to bool".format(a))

            elif type(a) == Decimal:
                new.append(bool(a))

            elif a is None:
                new.append(False)

            else:
                raise ValueError("{} cannot be converted to bool".format(a))
    return new

# functions to call - Boolean functions
def AND(*args):
    '''AND function'''
    if len(args) == 0:
        raise ValueError("AND needs at least 1 argument.")
    args = convert_to_bool(args)
    return reduce(lambda x, y: x and y, args)

def OR(*args):
    '''OR function'''
    if len(args) == 0:
        raise ValueError("OR needs at least one argument.")
    args = convert_to_bool(args)
    return reduce(lambda x, y: x or y, args)

def XOR(*args):
    '''XOR function'''
    if len(args) != 2:
        raise ValueError("XOR takes exactly 2 arguments.")
    args = convert_to_bool(args)
    return args[0] ^ args[1]

def NOT(*args):
    '''NOT function'''
    if len(args) != 1:
        raise ValueError("NOT takes exactly 1 argument.")
    args = convert_to_bool(args)
    return not args[0]

# helper function for string conversions
def convert_to_string(args):
    '''convert type to string for functions'''
    new = []
    for a in args:
        if type(a) == str:
            new.append(a)
        else:
            if type(a) == bool:
                if a:
                    new.append("TRUE")
                else:
                    new.append("FALSE")

            elif type(a) == Decimal:
                new.append(str(a))

            elif a is None:
                new.append("")

            else:
                raise ValueError("{} cannot be converted to string".format(a))

    return new

NON_NUMBERS = [Decimal("Infinity"), Decimal("Nan"),
    Decimal("-Infinity"), Decimal("-Nan")]

# helper function for number conversions
def convert_to_number(a):
    '''convert to number for functions'''
    new = []
    if type(a) == Decimal:
        new.append(a)
    else:
        if type(a) == bool:
            if a:
                new.append(Decimal(1))
            else:
                new.append(Decimal(0))

        elif type(a) == str:
            try:
                d = Decimal(a)
                if d not in NON_NUMBERS:
                    new.append(d)
            except:
                raise ValueError("{} cannot be converted to number".format(a))

        elif a is None:
            new.append(Decimal(0))

        else:
            raise ValueError("{} cannot be converted to number".format(a))

    return new[0]

# string functions
def EXACT(*args):
    '''EXACT function'''
    if len(args) != 2:
        raise ValueError("EXACT takes exactly 2 arguments.")
    args = convert_to_string(args)
    return args[0] == args[1]

# conditional notify_functions
def IF(*args):
    '''IF function'''
    if len(args) != 3:
        raise ValueError("IF takes exactly 3 arguments.")
    if (convert_to_bool([args[0]]))[0]:
        return args[1]
    else:
        return args[2]

def IFERROR(*args):
    '''IFERROR function'''
    if len(args) == 0 or len(args) > 2:
        raise ValueError("IFERROR takes 1 or 2 arguments.")

    if isinstance(args[0], CellError):
        if len(args) == 2:
            return args[1]
        else:
            return ""
    return args[0]

def CHOOSE(*args):
    '''CHOOSE function'''
    if len(args) < 2:
        raise ValueError("CHOOSE needs 1 or 2 arguments.")

    #print("CHOOSE args: ", args)

    index = convert_to_number(args[0])
    #if Decimal(int(index)) != index:
    #    raise ValueError("Index must be an integer")
    index = int(index)
    if index < 1 or index > len(args) - 1:
        raise ValueError("CHOOSE index out of range.")

    return args[index]

# Informational functions
def ISBLANK(*args):
    '''ISBLANK function'''
    if len(args) != 1:
        raise ValueError("ISBLANK needs exactly 1 argument.")


    return args[0] is None

def ISERROR(*args):
    '''ISERROR function'''
    if len(args) != 1:
        raise ValueError("ISERROR needs exactly 1 argument.")

    return isinstance(args[0], CellError)

def VERSION(*args):
    '''VERSION function'''
    if len(args) != 0:
        raise ValueError("VERSION takes 0 arguments.")

    return sheets.version

def combine_args_into_list(args):
    '''Combines lists and non-lists into one list. Also catches
       BAD_NAME errors in cell_ranges.'''
    values = []
    for a in args:
        if type(a) == list:
            # We have a nested cell_range list, so we flatten and add values
            a = [val for row in a for val in row]
            check_bad_name_cell_range(a)
            values += a
        else:
            values.append(a)
    return values

def check_bad_name_cell_range(cell_vals):
    '''Throws error if there is an error in the list of cell values'''
    for val in cell_vals:
        if is_error(val, CellErrorType.BAD_NAME):
            raise ValueError("cell range references bad cell")


def MIN(*args):
    '''MIN function'''
    args = combine_args_into_list(args)
    if len(args) < 1:
        raise ValueError("MIN needs at least 1 argument.")

    # All references are empty cells
    if set(args) == set([None]):
        return 0

    min = args[0]
    for a in args:
        if isinstance(a, CellError):
            raise ValueError("MIN encountered error")
        if compare(a, min, "<"):
            min = a
    return min

def MAX(*args):
    '''MAX function'''
    args = combine_args_into_list(args)
    if len(args) < 1:
        raise ValueError("MAX needs at least 1 argument.")

    # All references are empty cells
    if set(args) == set([None]):
        return 0

    max = args[0]
    for a in args:
        if isinstance(a, CellError):
            raise ValueError("MAX encountered error")
        if compare(a, max, ">"):
            max = a
    return max


def SUM(*args):
    args = combine_args_into_list(args)
    if len(args) < 1:
        raise ValueError("SUM needs least 1 argument.")

    # All references are empty cells
    if set(args) == set([None]):
        return 0

    args = [convert_to_number(a) for a in args]
    return sum(args)

def AVERAGE(*args):
    args = combine_args_into_list(args)
    if len(args) < 1:
        raise ValueError("AVERAGE needs at least 1 argument.")

    # All references are empty cells
    if set(args) == set([None]):
        return CellError(CellErrorType.DIVIDE_BY_ZERO, detail = 'AVERAGE given empty cells only')

    args = [convert_to_number(a) for a in args]
    return sum(args)/len(args)


def HLOOKUP(*args):
    if len(args) != 3:
        raise ValueError("HLOOKUP needs at least 3 argument.")

    # Get index as integer and check bounds
    index = int(convert_to_number(args[2]))
    key = args[0]
    grid = args[1]

    if type(grid) != list:
        raise ValueError("HLOOKUP takes cell range as second arg")
    if index < 1 or index > len(grid):
        raise ValueError("HLOOKUP index out of bounds")

    # Search though top row
    found_col = -1
    for i in range(len(grid[0])):
        ## TODO: potentially need to explicitly check for CellError type equality
        if grid[0][i] == key:
            found_col = i

    if found_col == -1:
        raise ValueError("HLOOKUP key not found in range")

    return grid[index - 1][found_col]


def VLOOKUP(*args):
    if len(args) != 3:
        raise ValueError("HLOOKUP needs at least 3 argument.")

    # Get index as integer and check bounds
    index = int(convert_to_number(args[2]))
    key = args[0]
    grid = args[1]

    if type(grid) != list:
        raise ValueError("VLOOKUP takes cell range as second arg")
    if index < 1 or index > len(grid[0]):
        raise ValueError("VLOOKUP index out of bounds")

    # Search though first column
    found_row = -1
    for i in range(len(grid)):
        ## TODO: potentially need to explicitly check for CellError type equality
        if grid[i][0] == key:
            found_row = i

    if found_row == -1:
        raise ValueError("VLOOKUP key not found in range")

    return grid[found_row][index - 1]


def get_func_dict():
    '''function dictionary to use in sheets'''
    func_dict = {}
    # boolean functions
    func_dict["AND"] = AND
    func_dict["OR"] = OR
    func_dict["XOR"] = XOR
    func_dict["NOT"] = NOT

    # string functions
    func_dict["EXACT"] = EXACT

    # conditional notify_functions
    func_dict["IF"] = IF
    func_dict["IFERROR"] = IFERROR
    func_dict["CHOOSE"] = CHOOSE

    # informational functions
    func_dict["ISBLANK"] = ISBLANK
    func_dict["ISERROR"] = ISERROR
    func_dict["VERSION"] = VERSION

    #Cell-range functions
    func_dict["MIN"] = MIN
    func_dict["MAX"] = MAX
    func_dict["SUM"] = SUM
    func_dict["AVERAGE"] = AVERAGE

    #Lookup functions
    func_dict["HLOOKUP"] = HLOOKUP
    func_dict["VLOOKUP"] = VLOOKUP




    return func_dict

func_dict = get_func_dict()
