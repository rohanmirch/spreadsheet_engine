'''Cell class and helper functions'''
from typing import Optional, Tuple
import re
from decimal import Decimal

class Cell:
    ''' Represents a cell in a sheets'''
    def __init__(self, contents = None):
        if contents == "":
            contents = None
        # remove whitespace
        self.contents = contents.strip() if contents is not None else None
        self.value = None
        # determines if the cell is a formula or not
        self.is_formula = self.contents[0] == \
            "=" if self.contents is not None else False
        self.children = [] # List of cell names that depend on cell
        self.parents = [] # List of cell names that current cell depends on
        self.bad_parents = []


def parse_cell_contents(contents: Optional[str]):
    '''Parses the contents string of a cell and returns the value
    not for formulas'''

    # empty contents
    if contents is None or contents.strip() == "":
        return None

    # otherwise, strip whiterspace
    contents = contents.strip()

    # parse depending on type
    if contents[0] == "=":
        return contents # Just return the formula as a string for now
    if contents[0] == "'":
        contents = contents[1:]
        if contents != "" and re.match("^-?\\d*(\\.\\d+)?$", contents) is not None:
            return Decimal('{:f}'.format(Decimal(contents).normalize()))
        else:
            return contents

    if contents.lower() == "false":
        return False
    if contents.lower() == "true":
        return True
    # try to make decimal
    if re.match("^-?\\d*(\\.\\d+)?$", contents) is not None:
        return Decimal('{:f}'.format(Decimal(contents).normalize()))
    return contents

## Helper functions for cell operations
def get_cell_tuple(location: str) -> Tuple[int, int]:
    '''Converts cell location string to tuple
     Throws ValueError if cell location is invalid'''

    # Split string in to letters and numbers
    location = location.lower()
    if " " in location:
        raise ValueError("Invalid cell format.")

    match = re.match(r"([a-z]+)([0-9]+$)", location, re.I)
    if not match:
        raise ValueError("Invalid cell format.")

    (col, row) = match.groups()
    if row[0] == "0":
        raise ValueError("Invalid cell format.")
    row = int(row)

    #Must convert column string (base 26) to integer
    alph = "abcdefghijklmnopqrstuvwxyz"  # or string.ascii_uppercase
    alph_index = {char: ind for ind, char in enumerate(alph, 1)}
    result = 0
    for char in col.lower():
        result = result * 26 + alph_index[char]
    col = result

    # Check validity
    if col < 1 or col > 475254 or row < 1 or row > 9999:
        raise ValueError("Cell location must be within A1 and ZZZZ9999.")

    return (col, row)

## Helper functions for cell operations
def get_cell_name(loc: Tuple[int, int]) -> str:
    '''Converts cell tuple to location string'''
    col, row = loc
    if col < 1 or row < 1:
        raise ValueError("Invalid location tuple: {}".format(loc))
    #must convert the column to letter value:
    loc_string = ""
    while col > 0:
        col, rem = divmod(col - 1, 26)
        loc_string = chr(65 + rem) + loc_string
    return loc_string + str(row)
