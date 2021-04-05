'''Formula parser for cells'''
import lark
from lark import Tree, Transformer
from decimal import Decimal, DecimalException
from .errors import CellError, CellErrorType
from .cell import get_cell_tuple, get_cell_name
from .helper_functions import get_empty_bool, compute_bool, compare, convert_to_string, is_error

parser = lark.Lark.open('formulas.lark', start='formula', rel_to=__file__)
NON_NUMBERS = [str(Decimal("Infinity")), str(Decimal("Nan")),
    str(Decimal("-Infinity")), str(Decimal("-Nan"))]

class eval_exp(Transformer):
    '''class to parse cell contents'''
    def __init__(self, wb = None, curr_sheet = ""):
        Transformer.__init__(self)
        self.wb = wb
        self.depends_on = []
        self.curr_sheet = curr_sheet
        self.parent_cells = []
        self.bad_cells = []
        #self.parser =  # Cells in a nonexistent sheet

    def expr(self, args):
        '''expression token'''
        return eval(args[0])

    def NUMBER(self, token):
        '''number token'''
        return Decimal(token) # Returns Tree("number", [Decimal])

    def STRING(self, token):
        '''string token'''
        return str(token)[1:-1]

    def BOOL(self, token):
        '''bool token'''
        if token.lower() == "false":
            return False
        return True


    def add_expr(self, args):
        '''Add expressions'''
        # Three arguments: [n1, +/-, n2]
        #n1 = self.transform(args[0]).children[-1]
        #n2 = self.transform(args[2]).children[-1]

        n1 = args[0].children[-1]
        n2 = args[2].children[-1]
        op = args[1]

        # Check for CellErrors
        if isinstance(n1, CellError):
            return Tree("cell_error", [n1])
        if isinstance(n2, CellError):
            return Tree("cell_error", [n2])

        # Type checking
        try:
            n1 = Decimal(n1) if n1 is not None else Decimal(0)
            n2 = Decimal(n2) if n2 is not None else Decimal(0)
            if str(n1) in NON_NUMBERS or str(n2) in NON_NUMBERS:
                raise ValueError("Mult/div with Infinity or NaN")
        except (ValueError, DecimalException):
            return Tree("cell_error", [CellError(CellErrorType.TYPE_ERROR,
                detail = "add/sub with non-numbers")])


        value = n1 + n2 if op == "+" else n1 - n2
        return Tree('number',
            [Decimal('{:f}'.format(Decimal(value).normalize()))])

    def mul_expr(self, args):
        '''Multiply expressions'''
        # Three arguments: [n1, *//, n2]
        n1 = self.transform(args[0]).children[-1]
        n2 = self.transform(args[2]).children[-1]
        op = args[1]

        # Check for CellErrors
        if isinstance(n1, CellError):
            return Tree("cell_error", [n1])
        if isinstance(n2, CellError):
            return Tree("cell_error", [n2])

        # Type checking
        try:
            n1 = Decimal(n1) if n1 is not None else Decimal(0)
            n2 = Decimal(n2) if n2 is not None else Decimal(0)
             #Check for Infinity or NaN in expression
            if str(n1) in NON_NUMBERS or str(n2) in NON_NUMBERS:
                raise ValueError("Mult/div with Infinity or NaN")
        except (ValueError, DecimalException):
            return Tree("cell_error", [CellError(CellErrorType.TYPE_ERROR,
                detail = "mult/div with non-numbers")])

        # Calculate value
        if op == "*":
            value = n1 * n2
        elif op == "/" and n2 != Decimal(0):
            value =  n1 / n2
        else:
            return Tree("cell_error", [CellError(CellErrorType.DIVIDE_BY_ZERO,
                detail = "Divide by zero in formula.")])


        return Tree('number',
            [Decimal('{:f}'.format(Decimal(value).normalize()))])

    def unary_op(self, args):
        '''Unary operations'''
        # Two arguments: [+-, n1]
        op = args[0]
        n1 = self.transform(args[1]).children[0]

        # Check for CellErrors
        if isinstance(n1, CellError):
            return Tree("cell_error", [n1])

        # Type checking
        try:
            n1 = Decimal(n1) if n1 is not None else Decimal(0)
            if str(n1) in NON_NUMBERS:
                raise ValueError("Mult/div with Infinity or NaN")
        except (ValueError, DecimalException):
            return Tree("cell_error", [CellError(CellErrorType.TYPE_ERROR,
                detail = "Unary with non-numbers")])

        value = -1 * n1 if op == "-" else n1
        return Tree('number', [value])

    def concat_expr(self, args):
        '''string concat'''
        # Two arguments: [s1, s2]
        # Take last child: will either be a value, or None if from empty cell
        s1 = self.transform(args[0]).children[-1]
        s2 = self.transform(args[1]).children[-1]

        # Check for CellErrors
        if isinstance(s1, CellError):
            return Tree("cell_error", [s1])
        if isinstance(s2, CellError):
            return Tree("cell_error", [s2])

        if type(s1) == bool:
            s1 = str(s1).upper()
        elif s1 is None:
            s1 = ""
        elif type(s1) == str:
            s1 = str(s1)
        else:
            s1 = '{:f}'.format(s1.normalize())

        if type(s2) == bool:
            s2 = str(s2).upper()
        elif s2 is None:
            s2 = ""
        elif type(s2) == str:
            s2 = str(s2)
        else:
            s2 = '{:f}'.format(s2.normalize())

        value = s1 + s2
        return Tree('string', [value])

    def compare_expr(self, args):
        '''comparing expressions'''
        # Three arguments: [n1, operator, n2]
        # Take last child: will either be a value, or None if from empty cell
        b1 = self.transform(args[0]).children[-1]
        b2 = self.transform(args[2]).children[-1]
        op = args[1]

        if isinstance(b1, CellError):
            return Tree("cell_error", [b1])
        if isinstance(b2, CellError):
            return Tree("cell_error", [b2])

        val = compare(b1, b2, op)


        return Tree('bool', [val])

    def function_expr(self, args):
        '''function expressions'''
        func_name = args[0]
        func_args = args[1]

        #raise ValueError(args)

        # NOTE: Arguments come in evaluated already, so no need to transform
        if func_args.data == "arg_list":
            args = [c.children[-1] for c in func_args.children]
        else:
            args = [func_args.children[-1]]

        # Directly deal with INDIRECT
        if func_name == "INDIRECT":
            return self.INDIRECT(func_args, len(args))

        if func_name not in self.wb.functions:
            return Tree("cell_error", [CellError(CellErrorType.BAD_NAME,
                detail = "Function does not exist")])

        try:
            val = self.wb.functions[func_name](*args)
        except ValueError as e:
            # Catch bad_name errors in cell ranges
            if "bad cell" in str(e):
                return Tree("cell_error", [CellError(CellErrorType.BAD_NAME,
                    detail = e)])
            # Any other error is a type error
            return Tree("cell_error", [CellError(CellErrorType.TYPE_ERROR,
                detail = e)])


        return Tree('func_val', [val])

    def INDIRECT(self, arg, num_args):
        ''' Computes INDIRECT '''
        if num_args != 1:
            return Tree("cell_error", [CellError(CellErrorType.TYPE_ERROR,
                detail = "INDIRECT takes exactly 1 argument.")])
        # We take the argument and check if it is a cell_ref
        if arg.data in ["cell_val","cell_error", "cell_list"]:
            return arg

        else: #basically: can it be converted to a string/is a string
            try:
                str_arg = convert_to_string(arg.children[0])
            except ValueError as e:
                return Tree("cell_error", [CellError(CellErrorType.TYPE_ERROR,
                    detail = e)])

            try:
                # We remove the quotes and parse the argument again
                tree = parser.parse("=INDIRECT(" + str_arg + ")")
                val = self.transform(tree)
                #If arg parses to a cell or cell_range, get that value
                if val.data in ["cell_val", "cell_error", "cell_list"]:
                    return Tree(val.data, [val.children[0]])
                else:
                    return Tree("cell_error", [CellError(CellErrorType.TYPE_ERROR,
                        detail = "INDIRECT requires a cell reference")])

            except lark.exceptions.LarkError:
            # If the string can not be parsed, it can't be a cell reference
                return Tree("cell_error", [CellError(CellErrorType.TYPE_ERROR,
                    detail = "INDIRECT requires a cell reference")])


    def CELLREF(self, token):
        '''How we parse the cells'''
        # Check cell then return CELLREF
        return token

    def NAME(self, token):
        '''Spreadsheet name'''
        return token

    def QUOTED_NAME(self, token):
        '''spreadsheet name with single quotes'''
        return token[1:-1]


    def cell_range(self, args):
        '''Cell range parsing. Returns a list of lists if cell range
           is valid. If not, returns a BAD_NAME error'''
        if len(args) == 1:
            sheet_name = self.curr_sheet
            cell_range = str(args[0])
        else:
            sheet_name = str(args[0])
            cell_range = str(args[1])

        #Get rid of $ because they don't affect the range
        cell_range = cell_range.replace("$", "").lower()
        cell1, cell2 = cell_range.split(":")

        try:
            c1 = get_cell_tuple(cell1)
            c2 = get_cell_tuple(cell2)
        except ValueError as e:
            return Tree("cell_list", [[[CellError(CellErrorType.BAD_NAME,
                detail = e)]]])

        top_left = (min(c1[0], c2[0]), min(c1[1], c2[1]))
        bottom_right = (max(c1[0], c2[0]), max(c1[1], c2[1]))

        # Go through and populate cell grid with cell values
        cells = []
        for row in range(top_left[1], bottom_right[1] + 1):
            row_vals = []
            for col in range(top_left[0], bottom_right[0] + 1):
                cell = get_cell_name((col, row))
                cell_val = self.cell([sheet_name, cell]).children[-1]
                row_vals.append(cell_val)
            cells.append(row_vals)

        values = cells
        return Tree("cell_list", [values])


    def cell(self, args):
        '''cell parsing'''
        if len(args) == 1:
            sheet_name = self.curr_sheet
            cell_name = str(args[0])
        else:
            sheet_name = str(args[0])
            cell_name = str(args[1])

        # Get rid of $ to find actual cell
        cell_name = cell_name.replace("$", "").lower()
        sheet_name = sheet_name.lower()
        try:
            val = self.wb.get_cell_value(sheet_name, cell_name)
            self.parent_cells.append((sheet_name, cell_name))
        except (KeyError, ValueError) as e:
            if "not in workbook" in str(e):
                val = CellError(CellErrorType.BAD_NAME,
                    detail = "{} does not exist".format(sheet_name))
                self.bad_cells.append((sheet_name, cell_name))
            else:
                # This happens if the sheet exists/cell does not exists
                # which indicates a bad_name error
                val = CellError(CellErrorType.BAD_NAME,
                    detail = "{} invalid cell".format(cell_name))

        if isinstance(val, CellError):
            return Tree("cell_error", [val])

        if val is None:
            return Tree("cell_val", [Decimal(0),None])

        return Tree("cell_val", [val])
