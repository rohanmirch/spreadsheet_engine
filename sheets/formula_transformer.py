'''Tranformer for renames or move/copy'''
import lark
from typing import Tuple
from lark import Tree, Transformer
from decimal import Decimal
import re

parser = lark.Lark.open('formulas.lark', start='formula', rel_to=__file__)
NON_NUMBERS = [str(Decimal("Infinity")), str(Decimal("Nan")),
    str(Decimal("-Infinity")), str(Decimal("-Nan"))]


#####################################################################
######## Transforms formulas for rename and move/copy operationa ###############

class transform_exp(Transformer):
    ''' This transformer updates formulas for either sheet renaming or cell
        moving. '''
    def __init__(self, old_sheet = None, new_sheet = None, shift = None):
        Transformer.__init__(self)
        self.old_sheet = old_sheet
        self.new_sheet = new_sheet

        ## CELL SHIFTING (if shift != none)
        self.depends_on = [] # Holds cell names (not tuples) that formula
                             # references will be used to set =#REF later
        self.shift = shift

    def expr(self, args):
        '''expresion'''
        return eval(args[0])

    def NUMBER(self, token):
        ''' Convert to string'''
        return str(token)

    def STRING(self, token):
        ''' Returns string as they are'''
        return str(token)

    def BOOL(self, token):
        '''convert to string'''
        return str(token)


    def add_expr(self, args):
        '''Add expression'''
        # Three arguments: [n1, +/-, n2]
        t1 = self.transform(args[0])
        t2 =  self.transform(args[2])
        n1 = t1.children[0]
        n2 = t2.children[0]
        op = args[1]

        # Add parenthesis to concat and bool operations only
        if len(t1.children) > 1 and t1.children[1] in ["c", "b"]:
            n1 = "({})".format(n1)
        if len(t2.children) > 1 and t2.children[1] in ["c", "b"]:
            n2 = "({})".format(n2)

        value = n1 + " " + op + " " + n2
        return Tree('string',[value, "a"])

    def mul_expr(self, args):
        '''Multiply expression'''
        # Three arguments: [n1, *//, n2]
        t1 = self.transform(args[0])
        t2 = self.transform(args[2])
        n1 = t1.children[0]
        n2 = t2.children[0]
        op = args[1]

        # Add parenthesis to concat and addition operations
        if len(t1.children) > 1 and (t1.children[1] in  ["c", "a", "b"]):
            n1 = "({})".format(n1)
        if len(t2.children) > 1 and (t2.children[1] in  ["c", "a", "b"]):
            n2 = "({})".format(n2)

        value = n1 + " " + op + " " + n2
        return Tree('string',[value, "m"])

    def unary_op(self, args):
        '''unary operators'''
        # Two arguments: [+-, n1]
        op = args[0]
        n1 = self.transform(args[1]).children[0]

        # Check for CellErrors
        value = op + n1
        return Tree('number', [value])

    def concat_expr(self, args):
        '''concat expression'''
        # Three arguments: [n1, *//, n2]
        t1 = self.transform(args[0])
        t2 = self.transform(args[1])
        n1 = t1.children[0]
        n2 = t2.children[0]

        # If one string is a methematical expression, it needs parenthesis
        if len(t1.children) > 1 and (t1.children[1] in  ["m", "a", "b"]):
            n1 = "({})".format(n1)
        if len(t2.children) > 1 and (t2.children[1] in ["m", "a", "b"]):
            n2 = "({})".format(n2)

        value = n1 + " " + "&" + " " + n2
        return Tree('string',[value, "c"])

    def compare_expr(self, args):
        '''compare expression'''
        # Three arguments: [n1, op, n2]
        t1 = self.transform(args[0])
        t2 = self.transform(args[2])
        n1 = t1.children[0]
        n2 = t2.children[0]
        op = args[1]

        # Add parenthesis to no operations because bool has lowest precedence
        value = n1 + " " + op + " " + n2
        return Tree('string',[value, "b"])

    def function_expr(self, args):
        '''function expression'''
        func_name = args[0]
        func_args = args[1]


        if len(func_args.children) != 1 and func_args.data != "string": #func_args is an arglist
            args = [c.children[0] for c in func_args.children]
        else: #Args is just a single tree
            args = [func_args.children[0]]

        func_string = func_name + "("
        if len(args) == 0:
            func_string += ")"
        else:
            func_string += args.pop(0)
            for a in args:
                func_string += ", " + a
            func_string += ")"

        return Tree("string", [func_string, "f"])


    def CELLREF(self, token):
        '''How we parse the cells'''
        # Check cell then return CELLREF
        return token

    def NAME(self, token):
        '''Spreadsheet name'''
        return token

    def CELLRANGE(self, token ):
        '''Parse cell ranges'''
        return token


    def QUOTED_NAME(self, token):
        '''spreadsheet name with single quote, different for rename and shift'''
        if self.shift is None:
            return self.QUOTED_NAME_rename(token)
        else:
            return self.QUOTED_NAME_shift(token)

    def QUOTED_NAME_rename(self, token):
        '''rename spreadsheet name with single quote'''
        # remove quotes, we will add them later if needed
        return token [1:-1]

    def QUOTED_NAME_shift(self, token):
        '''shift spreadsheet name with single quote'''
        # don't touch name
        return token


    def cell(self, args):
        '''cell shifting'''
        if self.shift is None:
            return self.cell_rename(args)
        else:
            return self.cell_shift(args)

    def cell_rename(self, args):
        ''' The "cell" function that is called when we are renaming sheets '''
        if len(args) == 1:
            sheet_name = ""
            cell_name = str(args[0])
            connector = ""
        else:
            sheet_name = str(args[0])
            cell_name = str(args[1])
            connector = "!"

        #Change the old sheet name to the new one
        sheet_name = sheet_name.lower()
        if sheet_name == self.old_sheet.lower():
            sheet_name = self.new_sheet

        # Add single quotes to sheet name if necessary (see project 1 spec)
        if sheet_name != "" and not (sheet_name[0].isalpha() and sheet_name.isalnum()):
            sheet_name = "'" + sheet_name + "'"


        val = sheet_name + connector + cell_name
        return Tree("cell_val", [val])

    def cell_shift(self, args):
        ''' The "cell" function that is called when we are shifting cells '''
        if len(args) == 1:
            sheet_name = ""
            cell_name = str(args[0])
            connector = ""
        else:
            sheet_name = str(args[0])
            cell_name = str(args[1])
            connector = "!"

        cell_ref = cell_name.replace("$", "").lower()
        col, row = get_cell_tup(cell_ref)

        final_cell = ""

        # Shift cell while taking abolute refrences into account
        # It either has 0, 1 or 2 "$"
        col_shift, row_shift = self.shift
        if cell_name.count("$") == 2: # Both absolute --> don't change
            final_cell = cell_name
        elif cell_name.count("$") == 1:
            if cell_name[0] == "$": # Column absolute only --> change row
                shifted_col, shifted_row = get_cell_str_tuple((col, row + row_shift))
                final_cell = "$" + shifted_col + shifted_row
            else: # Row abolute only --> change column
                shifted_col, shifted_row = get_cell_str_tuple((col + col_shift, row))
                final_cell = shifted_col + "$" + shifted_row
        else: # Neither absolute --> change both
            shifted_col, shifted_row = get_cell_str_tuple((col + col_shift, row + row_shift))
            final_cell = shifted_col + shifted_row


        # Add any cell refence to depends_on (for later OOB checks)
        self.depends_on.append(final_cell.replace("$", "").lower())

        val = sheet_name + connector + final_cell
        return Tree("cell_val", [val])

    def cell_range(self, args):
        if self.shift is None:
            # Don't touch the range, just sheet_name
            return self.cell_rename(args)
        else:
            #Shift both cells and combine again
            if len(args) == 1:
                sheet_name, connector, range = "", "", str(args[0])
            else:
                sheet_name, connector, range = str(args[0]), "!", str(args[1])

            #Shift cells individually and combine
            c1, c2 = range.split(":")
            c1 = self.cell_shift([c1]).children[0]
            c2 = self.cell_shift([c2]).children[0]
            val = sheet_name + connector + c1 + ":" + c2
            return Tree("cell_val", [val])





## Helper functions for cell operations
def get_cell_tup(location: str) -> Tuple[int, int]:
    '''Converts cell location string to tuple (without checking validity)
     Split string in to letters and numbers'''
    location = location.lower()
    match = re.match(r"([a-z]+)([0-9]+)", location, re.I)
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

    return (col, row)

## Helper functions for cell operations
def get_cell_str_tuple(loc: Tuple[int, int]) -> Tuple[str, str]:
    ''' Converts cell tuple to location string (without checking vailidity)'''
    col, row = loc
    loc_string = ""
    while col > 0:
        col, rem = divmod(col - 1, 26)
        loc_string = chr(65 + rem) + loc_string
    return loc_string, str(row)
