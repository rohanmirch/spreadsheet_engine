'''The workbook class that contains the workbook API for a spreadsheet engine.'''
from __future__ import annotations
from typing import List, Optional, Tuple, Any
from typing import TextIO, Callable, Iterable
import re
import json
import lark
import sheets
from .errors import CellError, CellErrorType
from .sheet import Sheet
from .functions import get_func_dict
from .cell import Cell, get_cell_tuple, parse_cell_contents, get_cell_name
from .sorting import rowProxy


from .formula_parser import eval_exp
from .formula_transformer import transform_exp


class Workbook:
    '''A workbook containing zero or more named spreadsheets.

    Any and all operations on a workbook that may affect calculated cell
    values should cause the workbook's contents to be updated properly.'''
    def __init__(self):
        '''Initialize a new empty workbook.'''

        self.sheets = {} # {Sheet names (lowercase keys only) : Sheet objects}
        self.sheet_list = [] # Holds sheet names (lowercase) for order
        self.pre_sheets = {} # hold sheets that don't exist but are referenced
        # Parses formulas
        self.parser = lark.Lark.open('formulas.lark',
            start='formula', rel_to=__file__)
        self.notify_functions = [] # hold notify functions
        self.functions = get_func_dict()
        self.update_dict = {}

    def num_sheets(self) -> int:
        '''Return the number of spreadsheets in the workbook.'''

        return len(self.sheets)

    def list_sheets(self) -> List[str]:
        '''Return a list of the spreadsheet names in the workbook, with the
        capitalization specified at creation, and in the order that the sheets
        appear within the workbook.

        In this project, the sheet names appear in the order that the user
        created them; later, when the user is able to move and copy sheets,
        the ordering of the sheets in this function's result will also reflect
        such operations.'''

        # Iterate through ordered sheet list to get uppercase names
        return [self.sheets[s].name for s in self.sheet_list]

    def _get_new_sheet_name(self, sheet_name):
        '''Check validity of new sheet name, generates it if needed,
           then returns it.'''

        if sheet_name is not None:
            # wrong characters
            if not re.match(r"^[a-zA-Z0-9.?!, :;!@#$%^&*()-]+$",
                sheet_name) or sheet_name != sheet_name.strip():
                raise ValueError("Sheet name invalid.")
            # already exists
            if sheet_name.lower() in self.sheets:
                raise ValueError("Sheet name already exists.")
        else:
            # Generate unique sheet name
            i = 1
            while True:
                sheet_name = "Sheet" + str(i)
                if sheet_name.lower() not in self.sheets:
                    break
                i += 1

        return sheet_name

    def new_sheet(self, sheet_name: Optional[str] = None, copy = False) -> Tuple[int, str]:
        '''Add a new sheet to the workbook.  If the sheet name is specified, it
        must be unique.  If the sheet name is None, a unique sheet name is
        generated.  "Uniqueness" is determined in a case-insensitive manner,
        but the case specified for the sheet name is preserved.

        The function returns a tuple with two elements:
        (0-based index of sheet in workbook, sheet name).  This allows the
        function to report the sheet's name when it is auto-generated.

        If the spreadsheet name is an empty string (not None), or it is
        otherwise invalid, a ValueError is raised.'''

        # Check for invalid sheet names and get sheet_name if necessary
        sheet_name = self._get_new_sheet_name(sheet_name)

        # Add sheet to dictionary with lowercase key
        if sheet_name.lower() in self.pre_sheets:
            # If the sheet was already referenced, transfer it over and
            # delete it from pre-sheets
            self.sheets[sheet_name.lower()] = \
                self.pre_sheets[sheet_name.lower()]
            self.sheets[sheet_name.lower()].name = sheet_name
            del self.pre_sheets[sheet_name.lower()]

        else:
            # Create new sheet
            self.sheets[sheet_name.lower()] = Sheet(sheet_name)

        self.sheet_list.append(sheet_name.lower())

        # Go though and update any cells that already existed in the new sheet
        new_sheet = self.sheets[sheet_name.lower()]
        for cell in new_sheet.cells:
            try:
                self.set_cell_contents(sheet_name, cell, None, update_cell = True)
            except (ValueError, KeyError):
                # If the cell contents is invalid, discard the cell
                # by not instantiating it
                pass

        return len(self.sheets) - 1, sheet_name

    def del_sheet(self, sheet_name: str) -> None:
        '''Delete the spreadsheet with the specified name.

        The sheet name match is case-insensitive; the text must match but the
        case does not have to.

        If the specified sheet name is not found, a KeyError is raised.'''

        if sheet_name.lower() not in self.sheets:
            raise KeyError("Sheet {} not in workbook.".format(sheet_name))

        del_sheet = self.sheets[sheet_name.lower()]
        del self.sheets[sheet_name.lower()]

        self.pre_sheets[sheet_name.lower()] = del_sheet

        for cell in del_sheet.cells:
            # Update the children of the cells in the now-deleted sheet
            children = del_sheet.cells[cell].children
            for c_sheet, c_name in children:
                # Only update children in active sheet
                if c_sheet in self.sheets:
                    child = self.sheets[c_sheet].cells[c_name]
                    self.set_cell_contents(c_sheet, c_name, child.contents, update_cell = True)

        self.sheet_list.remove(sheet_name.lower())

    def _get_formula_new_sheet(self, contents, old_sheet, new_sheet):
        ''' Transforms fomula contents to have new_sheet instead of old_sheet.'''

        try:
            tree = self.parser.parse(contents)
        except lark.exceptions.LarkError:
            # Don't touch unparseable formulas
            return contents
        # Update formula
        evaluator = transform_exp(old_sheet = old_sheet, new_sheet = new_sheet)
        final_eval = evaluator.transform(tree)
        return "=" + final_eval.children[0]



    def rename_sheet(self, sheet_name: str, new_sheet_name: str) -> None:
        '''Rename the specified sheet to the new sheet name.  Additionally, all
        cell formulas that referenced the original sheet name are updated to
        reference the new sheet name (using the same case as the new sheet
        name, and single-quotes iff [if and only if] necessary).

        The sheet_name match is case-insensitive; the text must match but the
        case does not have to.

        As with new_sheet(), the case of the new_sheet_name is preserved by
        the workbook.

        If the sheet_name is not found, a KeyError is raised.

        If the new_sheet_name is an empty string or is otherwise invalid, a
        ValueError is raised.'''


        # Check for invalid sheet names and get new_sheet_name if necessary
        if sheet_name.lower() not in self.sheets:
            raise KeyError("Sheet {} not in workbook.".format(sheet_name))
        new_sheet_name = self._get_new_sheet_name(new_sheet_name)

        # Update dictionary and delete old sheet key
        sheet = self.sheets[sheet_name.lower()]
        self.sheets[new_sheet_name.lower()] = sheet
        sheet.name = new_sheet_name
        del self.sheets[sheet_name.lower()]

        # Update sheet list
        self.sheet_list[self.sheet_list.index(sheet_name.lower())] = new_sheet_name.lower()

        #Process:
        # 1. Go through all cells of sheet
        #  - Update contents (get new contents): replace sheet names
        #  - delete children in same sheet (they will be added later), delete all parents
        #  - Update contents of out-of sheet children (in sheet children will be updated in loop)
        #    - Update both formula and parents

        # 2. Set cell value for every cell in sheet
        #    - set cell value to contents - will update its children as well
        #    - will also add children to parents in same sheet
        for cell in sheet.cells:
            curr_cell = sheet.cells[cell]
            if curr_cell.is_formula and sheet_name.lower() in curr_cell.contents.lower():

                # Update formula contents if necessary
                new_formula = self._get_formula_new_sheet(curr_cell.contents, sheet_name, \
                        new_sheet_name)
                curr_cell.contents = new_formula

            # Delete children in same sheet, they will be added later when setting values
            curr_cell.children = [(s_name, cell) for s_name, cell in \
                curr_cell.children if s_name != sheet_name.lower()]
            curr_cell.parents = []

            for c_sheet, c_cell in curr_cell.children:
                try:
                    child_cell = self.sheets[c_sheet].cells[c_cell]
                except KeyError:
                    continue # Dead child -- we should deal with this in del_sheet()
                if child_cell.is_formula:
                    # Update formula contents and child's parents to have renamed sheet
                    new_formula = self._get_formula_new_sheet(child_cell.contents, \
                            sheet_name, new_sheet_name)

                    child_cell.contents = new_formula
                    child_cell.parents = [(s_name, cell) if s_name != sheet_name.lower() else \
                        (new_sheet_name.lower(), cell) for s_name, cell in child_cell.parents ]


        # Update value of all cells in sheets
        # This will 1) connect children to parents ands 2) update children in other sheets
        for cell in sheet.cells:
            curr_cell = sheet.cells[cell]
            self.set_cell_contents(new_sheet_name, cell, curr_cell.contents, bulk_op = True)


        # Deal with cells that referenced the new name sheet before they were new
        if new_sheet_name.lower() in self.pre_sheets:
            for cell in self.pre_sheets[new_sheet_name.lower()].cells:
                cell_obj= self.pre_sheets[new_sheet_name.lower()].cells[cell]
                for c_sheet, c_cell in cell_obj.children:
                    try:
                        child_cell = self.sheets[c_sheet].cells[c_cell]
                        if child_cell.is_formula:
                            # Update formula contents and child's parents to have renamed sheet
                            new_formula = self._get_formula_new_sheet(child_cell.contents, \
                                    sheet_name, new_sheet_name)
                            self.set_cell_contents(c_sheet, c_cell, new_formula, bulk_op = True, update_cell = True)

                    except KeyError:
                        continue

        self._process_update_dict()

    def move_sheet(self, sheet_name: str, index: int) -> None:
        '''Move the specified sheet to the specified index in the workbook's
        ordered sequence of sheets.  The index can range from 0 to
        workbook.num_sheets() - 1.  The index is interpreted as if the
        specified sheet were removed from the list of sheets, and then
        re-inserted at the specified index.

        The sheet name match is case-insensitive; the text must match but the
        case does not have to.

        If the specified sheet name is not found, a KeyError is raised.

        If the index is outside the valid range, an IndexError is raised.'''

        if sheet_name.lower() not in self.sheets:
            raise KeyError("Sheet {} not in workbook.".format(sheet_name))

        if index < 0 or index > self.num_sheets() - 1:
            raise IndexError("Sheet index {} out of range.".format(index))

        self.sheet_list.remove(sheet_name.lower())
        self.sheet_list.insert(index, sheet_name.lower())


    def copy_sheet(self, sheet_name: str) -> Tuple[int, str]:
        '''Make a copy of the specified sheet, storing the copy at the end of the
        workbook's sequence of sheets.  The copy's name is generated by
        appending "-1", "-2", ... to the original sheet's name (preserving the
        original sheet name's case), incrementing the number until a unique
        name is found.  As usual, "uniqueness" is determined in a
        case-insensitive manner.

        The sheet name match is case-insensitive; the text must match but the
        case does not have to.

        Like new_sheet(), this function returns a tuple with two elements:
        (0-based index of copy in workbook, copy sheet name).  This allows the
        function to report the new sheet's name and index in the sequence of
        sheets.

        If the specified sheet name is not found, a KeyError is raised.'''

        if sheet_name.lower() not in self.sheets:
            raise KeyError("Sheet {} not in workbook.".format(sheet_name))

        sheet_name = self.sheets[sheet_name.lower()].name
        incr = 1
        new_name = sheet_name + "-" + str(incr)
        while new_name.lower() in self.sheets:
            incr += 1
            new_name = sheet_name + "-" + str(incr)

        # Make new sheet and add it in to dictionary and list
        # just use self.new_sheet() --> it takes care of pre_sheets that already
        #  have cells that are referenced by other
        self.new_sheet(new_name)

        # Go through and set cells in new sheet as the old ones
        for cell in self.sheets[sheet_name.lower()].cells:
            old_cell = self.sheets[sheet_name.lower()].cells[cell]
            self.set_cell_contents(new_name, cell, old_cell.contents)

        return (len(self.sheet_list)-1, new_name)


    def get_sheet_extent(self, sheet_name: str) -> Tuple[int, int]:
        '''Return a tuple (num-cols, num-rows) indicating the current extent of
        the specified spreadsheet.

        The sheet name match is case-insensitive; the text must match but the
        case does not have to.

        If the specified sheet name is not found, a KeyError is raised.'''

        if sheet_name.lower() not in self.sheets:
            raise KeyError("Sheet {} not in workbook.".format(sheet_name))
        return self.sheets[sheet_name.lower()].get_extent()

    def set_cell_contents(self, sheet_name: str, location: str,
                          contents: Optional[str], bulk_op = False, update_cell = False) -> None:
        '''Set the contents of the specified cell on the specified sheet,
        and updates the sheet's extent.

        The sheet name match is case-insensitive; the text must match but the
        case does not have to.  Additionally, the cell location can be
        specified in any case.

        If the specified sheet name is not found, a KeyError is raised.
        If the cell location is invalid, a ValueError is raised.

        A cell may be set to "empty" by specifying a contents of None.

        Leading and trailing whitespace are removed from the contents before
        storing them in the cell.  Storing a zero-length string "" (or a
        string composed entirely of whitespace) should result in setting the
        cell contents to None.

        If the cell contents appear to be a formula, and the formula is
        invalid for some reason, this method does not raise an exception;
        rather, the cell's value will be a CellError object indicating the
        naure of the issue.

        If set_cell_contents is called by a bulk operation:
        move, copy, rename, sort'''
        ## Check sheet + location validity and raise necessary errors
        sheet_name = sheet_name.lower()
        location = location.lower()

        if not update_cell and contents == self.get_cell_contents(sheet_name, location):
            return None

        #self.update_dict = {}
        if (sheet_name, location) not in self.update_dict:
            self.update_dict[(sheet_name, location)] = [self.get_cell_value(sheet_name, location)]
        else:
            self.update_dict[(sheet_name, location)].append(self.get_cell_value(sheet_name, location))

        # Store the previous cell (for children transfer)
        prev_cell = None
        if location.lower() in self.sheets[sheet_name].cells:
            prev_cell = self.sheets[sheet_name].cells[location]


        # Create the new cell (which sets the contents), carry over children,
        # add to sheet
        new_cell = Cell(contents = contents)
        if prev_cell is not None:
            new_cell.children = prev_cell.children[:]
        self.sheets[sheet_name].cells[location] = new_cell

        ################### VALUE SETTING ############
        # Set initial value (set to either number or string)
        new_cell.value = parse_cell_contents(new_cell.contents)
        bad_cells = []
        if new_cell.is_formula:
            try:
                tree = self.parser.parse(new_cell.contents)
                # create evaluator object (that has access to current wb)
                evaluator = eval_exp(wb = self, curr_sheet = sheet_name)
                final_eval = evaluator.transform(tree)
                new_cell.value = final_eval.children[0]
                # If the value is a cell_range object (list of lists), it is TYPE_ERR0R
                if type(new_cell.value) == list:
                    new_cell.value = CellError(CellErrorType.TYPE_ERROR, detail =
                    "function received cell range")

                new_cell.parents = list(set(evaluator.parent_cells))
                # cells that are in a nonexistent sheet
                bad_cells = list(set(evaluator.bad_cells))


            except lark.exceptions.LarkError as e:
                # Indicates that the formula cannot be parsed
                new_cell.value = CellError(CellErrorType.PARSE_ERROR,
                    detail = "Can not parse {}".format(contents))
                #raise e

        ### TAKE care of cells in nonexistent sheets
        for b_sheet, b_cell in bad_cells:
            # Make new pre_sheet if necessary
            if b_sheet not in self.pre_sheets:
                self.pre_sheets[b_sheet] = Sheet(name = b_sheet)
            # Make (or find) the referenced cell in the nonexistent sheet
            non_sheet = self.pre_sheets[b_sheet]
            if b_cell not in non_sheet.cells:
                new_bad_cell = Cell()
                ## For now, set the nonexistent cells to None instead of BAD_NAME
                #  (for cell update notification purposes)
                new_bad_cell.value = None #CellError(CellErrorType.BAD_NAME)
                non_sheet.cells[b_cell] = new_bad_cell
            else:
                new_bad_cell = non_sheet.cells[b_cell]

            # Add the current cell to the children of the bad cell
            new_bad_cell.children.append((sheet_name, location))
            new_bad_cell.children = list(set(new_bad_cell.children))
        new_cell.bad_parents = bad_cells

        ## Update children of parents
        for p_sheet, p_cell in new_cell.parents:
            if p_cell.lower() not in self.sheets[p_sheet.lower()].cells:
                self.sheets[p_sheet.lower()].cells[p_cell.lower()] = \
                    Cell(contents = None)
            parent_cell = self.sheets[p_sheet.lower()].cells[p_cell.lower()]
            parent_cell.children.append((sheet_name, location))
            #remove duplicates
            parent_cell.children = list(set(parent_cell.children))

        ## Remove current cell from cells that are no longer parents (dead parents)
        if prev_cell is not None:
            dead_parents = list(set(prev_cell.parents) - set(new_cell.parents) - set(bad_cells))
            for p_sheet, p_cell in dead_parents:
                if p_cell.lower() not in self.sheets[p_sheet.lower()].cells:
                    self.sheets[p_sheet.lower()].cells[p_cell.lower()] = \
                        Cell(contents = None)
                parent_cell = self.sheets[p_sheet.lower()].cells[p_cell.lower()]
                parent_cell.children.remove((sheet_name, location))



        ## Check for circular dependency, get list of descendants
        circ_dep = False
        desc = []
        queue = [(sheet_name, location)]
        while queue != []:
            #print("detection bfs")
            curr_cell = queue.pop(0)
            sheet, cell = curr_cell
            try:
                child = self.sheets[sheet.lower()].cells[cell]
            except KeyError:
                # Child in nonexistent sheet (Dead child), so continue
                # when we delete a sheet, just delete cells from parents
                continue

            if isinstance(child.value, CellError):
                if child.value.get_type() == CellErrorType.CIRCULAR_REFERENCE:
                # If we run into circular reference
                    continue

            if desc != [] and curr_cell == desc[0]:
                # Circular dependency: we reached the current cell again
                circ_dep = True
                break

            desc.append(curr_cell)
            queue += self.sheets[curr_cell[0]].cells[curr_cell[1]].children

            # Wan't to remove duplicates in queue.
            queue = list(dict.fromkeys(queue))


        ## Update value of current cell if circular dependency
        if circ_dep:
            new_cell.value = CellError(CellErrorType.CIRCULAR_REFERENCE,
                detail = "Circ. ref")

        self.update_dict[(sheet_name, location)].append(new_cell.value)

        ## Update descendants using BFS
        queue = new_cell.children[:]
        while queue != []:
            #print("update bfs")
            curr_cell = queue.pop(0)
            sheet, cell = curr_cell

            # If we reach the current cell again, ignore it
            if curr_cell == (sheet_name, location):
                continue
            try:
                child = self.sheets[sheet.lower()].cells[cell]
            except KeyError:
                # Dead child, so ignore
                continue

            # Fill cell update dictionary with initial value of descendent
            if (sheet.lower(), cell.lower()) not in self.update_dict:
                self.update_dict[sheet.lower(), cell.lower()] = [child.value]


            # Check to see if it was previously a circular ref error
            was_error = False
            if isinstance(child.value, CellError):
                if child.value.get_type() == CellErrorType.CIRCULAR_REFERENCE:
                    was_error = True

            old_val = child.value
            # Update child value
            try:
                tree = self.parser.parse(child.contents)
                evaluator = eval_exp(wb = self, curr_sheet = sheet)
                final_eval = evaluator.transform(tree)
                child.value = final_eval.children[0]
                # If the value is a cell_range object (list of lists), it is TYPE_ERR0R
                if type(child.value) == list:
                    child.value = CellError(CellErrorType.TYPE_ERROR, detail =
                    "function received cell range")
            except lark.exceptions.LarkError:
                child.value = CellError(CellErrorType.PARSE_ERROR,
                    detail = "Can not parse {}".format(contents))


            if bool(set(child.parents) & set(child.children)):
                child.value = CellError(CellErrorType.CIRCULAR_REFERENCE,
                    detail = "Circ. ref detected")

            # Add updated child
            self.update_dict[sheet.lower(), cell.lower()].append(child.value)

            # If we run into a cell that has always been a circular reference,
            # don't append children. Otherwise, we need to keep updating its
            # children to allow the circular ref error to propagate
            if isinstance(child.value, CellError):
                if child.value.get_type() == \
                            CellErrorType.CIRCULAR_REFERENCE and was_error:
                    continue

            if child.value == old_val:
                continue

            queue += self.sheets[curr_cell[0]].cells[curr_cell[1]].children
            queue = list(dict.fromkeys(queue))

        if bulk_op == False:
            self._process_update_dict()

    def _process_update_dict(self):
        # Go though update dictionary and find changed cells
        changed_cells = []
        for cell_tup in self.update_dict:
            cell_vals = self.update_dict[cell_tup]

            # Both are errors, so check type
            if isinstance(cell_vals[0], CellError) and isinstance(cell_vals[1], CellError):
                if cell_vals[0].get_type() != cell_vals[1].get_type():
                    changed_cells.append(cell_tup)
            else:
                if cell_vals[0] != cell_vals[-1]:
                    changed_cells.append(cell_tup)

        # Get actual sheet names and cells
        changed = [(self.sheets[s].name, cell.upper()) for s, cell in changed_cells]
        # Call helper function to notify registered cell change functions
        self._cell_notification_helper(changed)
        self.update_dict = {}


    def _cell_notification_helper(self, changed_cells):
        ''' Takes in list of (sheet name, cell) tuples and calls all
            notifcation functions in self.notify_functions.'''

        for function in self.notify_functions:
            try:
                function(self, changed_cells)
            except Exception: #for any type of function exception
                pass

    def get_cell_contents(self, sheet_name: str, location: str) -> Optional[str]:
        '''Return the contents of the specified cell on the specified sheet.

        The sheet name match is case-insensitive; the text must match but the
        case does not have to.  Additionally, the cell location can be
        specified in any case.

        If the specified sheet name is not found, a KeyError is raised.
        If the cell location is invalid, a ValueError is raised.

        This method will never return a zero-length string; instead, empty
        cells are indicated by a value of None.'''

        sheet_name = sheet_name.lower()
        if sheet_name.lower() not in self.sheets:
            raise KeyError("Sheet {} not in workbook.".format(sheet_name))
        get_cell_tuple(location)

        if location.lower() not in self.sheets[sheet_name].cells:
            return None

        return self.sheets[sheet_name].cells[location.lower()].contents

    def get_cell_value(self, sheet_name: str, location: str) -> Any:
        '''Return the evaluated value of the specified cell on the specified
        sheet.

        The sheet name match is case-insensitive; the text must match but the
        case does not have to.  Additionally, the cell location can be
        specified in any case.

        If the specified sheet name is not found, a KeyError is raised.
        If the cell location is invalid, a ValueError is raised.

        The value of empty cells is None.  Non-empty cells may contain a
        value of str, decimal.Decimal, or CellError.'''

        sheet_name = sheet_name.lower()
        if sheet_name.lower() not in self.sheets:
            raise KeyError("Sheet {} not in workbook.".format(sheet_name))
        get_cell_tuple(location)

        if location.lower() not in self.sheets[sheet_name].cells:
            return None
        return self.sheets[sheet_name].cells[location.lower()].value


    @staticmethod
    def load_workbook(fp: TextIO) -> Workbook:
        '''This is a static method (not an instance method) to load a workbook
        from a text file or file-like object in JSON format, and return the
        new Workbook instance.

        If the contents of the input cannot be parsed by the Python json
        module then a json.JSONDecodeError should be raised by the method.
        (Just let the json module's exceptions propagate through.)  Similarly,
        if an IO read error occurs (unlikely but possible), let any raised
        exception propagate through.

        If any expected value in the input JSON is missing (e.g. a sheet
        object doesn't have the "cell-contents" key), raise a KeyError with
        a suitably descriptive message.

        If any expected value in the input JSON is not of the proper type
        (e.g. an object instead of a list, or a number instead of a string),
        raise a TypeError with a suitably descriptive message.'''


        # create workbook to fill and return
        wb = Workbook()

        # load in file contents or reports errors
        js = json.load(fp)

        # check for version
        if 'version' not in js:
            raise KeyError("Version contents missing")

        # check version type
        if not isinstance(js['version'], str):
            raise TypeError("Version should be a string")

        # check for sheets
        if 'sheets' not in js:
            raise KeyError("Sheet contents missing")

        # check sheets type
        if not isinstance(js['sheets'], list):
            raise TypeError("Sheets should be a list")

        # check version (not sure if necessary)
        #if float(js['version']) > float(sheets.version):
          #  raise ValueError("Version not compatible")

        # go through sheets
        for sheet in js["sheets"]:

            # make sure sheet is a dictionary
            if not isinstance(sheet, dict):
                raise TypeError("Sheet contents should be a dictionary")

            # check for name
            if 'name' not in sheet:
                raise KeyError("Sheet name contents missing")

            # check type of name
            if not isinstance(sheet['name'], str):
                raise TypeError("Sheet name should be a string")

            # check for cell contents
            if 'cell-contents' not in sheet:
                raise KeyError("Sheet cell contents missing")

            # check cell contents type
            if not isinstance(sheet['cell-contents'], dict):
                raise TypeError("Cell contents value should be a dictionary")

            # all good so create sheet and fill contents
            (_index, name) = wb.new_sheet(sheet["name"])

            # add cell contents
            for location in sheet['cell-contents']:

                # check cell type
                if not isinstance(location, str):
                    raise TypeError("Cell location should be string")

                # check cell content type
                if not isinstance(sheet['cell-contents'][location], str):
                    raise TypeError("Cell contents at given location should be string")

                # all good, so add contents
                wb.set_cell_contents(name, location, sheet['cell-contents'][location])

        return wb


    def save_workbook(self, fp: TextIO) -> None:
        '''Instance method (not a static/class method) to save a workbook to a
        text file or file-like object in JSON format.

        If an IO write error occurs (unlikely but possible), let any raised
        exception propagate through.'''

        # create dictionary to output to json
        output = {}

        # get the version
        output["version"] = sheets.version

        # create sheets
        output["sheets"] = []

        # add sheets and contents in order
        for sheet in self.sheet_list:

            # create dictionary to add
            json_sheet = {}

            # add name
            json_sheet["name"] = self.sheets[sheet].name

            # add cell contents
            json_sheet["cell-contents"] = {}

            for cell in self.sheets[sheet].cells:
                if self.get_cell_value(sheet, cell) is not None:
                    # add non-empty cell
                    json_sheet["cell-contents"][cell.upper()] = \
                        self.get_cell_contents(self.sheets[sheet].name, cell)

            # add to list
            output["sheets"].append(json_sheet)

        # dump to file
        json.dump(output, fp)


    def notify_cells_changed(self,
            notify_function: Callable[Workbook, Iterable[Tuple[str, str]]]) -> None:
        '''Request that all changes to cell values in the workbook are reported
        to the specified notify_function.  The values passed to the notify
        function are the workbook, and an iterable of 2-tuples of strings,
        of the form ([sheet name], [cell location]).

        Multiple notification functions may be registered on the workbook;
        functions will be called in the order that they are registered.

        A given notification function may be registered more than once; it
        will receive each notification as many times as it was registered.

        If the notify_function raises an exception while handling a
        notification, this will not affect workbook calculation updates or
        calls to other notification functions.

        A notification function is expected to not mutate the workbook or
        iterable that it is passed to it.  If a notification function violates
        this requirement, the behavior is undefined.'''

        # add function to list to be called in modifying functions
        self.notify_functions.append(notify_function)

    def _get_formula_shift_cells(self, contents, shift):
        ''' Transforms formula contents to shift cell refrences, then
            return shifted formula.'''

        try:
            tree = self.parser.parse(contents)
        except lark.exceptions.LarkError:
            # Don't touch unparseable formulas --> will be PARSE_ERROR
            return contents
        # Update formula
        evaluator = transform_exp(shift = shift)
        final_eval = evaluator.transform(tree)

        # check if references a cell that is out of bounds
        try:
            [get_cell_tuple(cell) for cell in evaluator.depends_on]
        except ValueError:
            return '="#REF!"'

        return "=" + final_eval.children[0]

    def _shift_cells_helper(self, sheet_name: str, start_location: str,
            end_location: str, to_location: str, to_sheet: Optional[str] = None):
        ''' Helper function that does steps 1-4 described in move_cells
            copy_cells.  '''

        if sheet_name.lower() not in self.sheets:
            raise KeyError("Sheet {} not in workbook.".format(sheet_name))
        if to_sheet is not None and to_sheet.lower() not in self.sheets:
            raise KeyError("Sheet {} not in workbook.".format(to_sheet))
        if to_sheet is None:
            to_sheet = sheet_name

        ## Process:
        # 1. Use corners to get boundaries, shift distance
        # 2. Get coordinates of Cells
        # 3. Get coordinates of shifted cells (+ check for shifting out of bounds)
        # 4. For each shifted location:
        #   - get new contents (+ set to #REF if needed)
        # 5. Go through original cells and set_cell_contents to None
        #   - Children/parents taken care of by set_cell_contents()
        # 6. Go through shifted cells an set_cell_contents() to contents we calculated
        #  - Takes care of parents/children


        c1 = get_cell_tuple(start_location)
        c2 = get_cell_tuple(end_location)
        target = get_cell_tuple(to_location)

        top_left = (min(c1[0], c2[0]), min(c1[1], c2[1]))
        bottom_right = (max(c1[0], c2[0]), max(c1[1], c2[1]))

        source_tuples = []
        for col in range(top_left[0], bottom_right[0] + 1):
            for row in range(top_left[1], bottom_right[1] + 1):
                source_tuples.append((col, row))

        source_cells = [get_cell_name(tup) for tup in source_tuples]

        # Calculate the cells to move to (shifted cells)
        col_shift = target[0]-top_left[0]
        row_shift = target[1]-top_left[1]
        shift = (col_shift, row_shift)
        shifted_tuples = [(tup[0]+shift[0], tup[1]+shift[1]) for tup in source_tuples]
        shifted_cells = [get_cell_name(tup) for tup in shifted_tuples]

        ### Check for out of bounds errors in target cells
        try:
            [get_cell_tuple(tup) for tup in shifted_cells]
        except ValueError:
            raise ValueError("Target cells out of bounds.")

        # Go though cells and get new contents (step 4)
        shifted_contents = []
        for cell in source_cells:
            cont = self.get_cell_contents(sheet_name, cell)
            if cont is not None and cont[0] == "=":
                cont = self._get_formula_shift_cells(cont, shift)
            shifted_contents.append(cont)

        return source_cells, shifted_cells, shifted_contents


    def move_cells(self, sheet_name: str, start_location: str,
            end_location: str, to_location: str, to_sheet: Optional[str] = None) -> None:
        '''Move cells from one location to another, possibly moving them to
        another sheet.  All formulas in the area being moved will also have
        all relative and mixed cell-references updated by the relative
        distance each formula is being copied.

        Cells in the source area (that are not also in the target area) will
        become empty due to the move operation.

        The start_location and end_location specify the corners of an area of
        cells in the sheet to be moved.  The to_location specifies the
        top-left corner of the target area to move the cells to.

        Both corners are included in the area being moved; for example,
        copying cells A1-A3 to B1 would be done by passing
        start_location="A1", end_location="A3", and to_location="B1".

        The start_location value does not necessarily have to be the top left
        corner of the area to move, nor does the end_location value have to be
        the bottom right corner of the area; they are simply two corners of
        the area to move.

        This function works correctly even when the destination area overlaps
        the source area.

        The sheet name matches are case-insensitive; the text must match but
        the case does not have to.

        If to_sheet is None then the cells are being moved to another
        location within the source sheet.

        If any specified sheet name is not found, a KeyError is raised.
        If any cell location is invalid, a ValueError is raised.

        If the target area would extend outside the valid area of the
        spreadsheet (i.e. beyond cell ZZZZ9999), a ValueError is raised, and
        no changes are made to the spreadsheet.'''

        source_cells, shifted_cells, shifted_contents = \
        self._shift_cells_helper(sheet_name, start_location, \
        end_location, to_location, to_sheet  = to_sheet)

        if to_sheet is None:
            to_sheet = sheet_name

        ## Set original sell contents to none
        for cell in list(set(source_cells) - set(shifted_cells)):
            self.set_cell_contents(sheet_name, cell, None, bulk_op = True)

        for i, cell in enumerate(shifted_cells):
            self.set_cell_contents(to_sheet, cell, shifted_contents[i], bulk_op = True)

        self._process_update_dict()

    def copy_cells(self, sheet_name: str, start_location: str,
            end_location: str, to_location: str, to_sheet: Optional[str] = None) -> None:
        '''Copy cells from one location to another, possibly copying them to
        another sheet.  All formulas in the area being copied will also have
        all relative and mixed cell-references updated by the relative
        distance each formula is being copied.

        Cells in the source area (that are not also in the target area) are
        left unchanged by the copy operation.

        The start_location and end_location specify the corners of an area of
        cells in the sheet to be copied.  The to_location specifies the
        top-left corner of the target area to copy the cells to.

        Both corners are included in the area being copied; for example,
        copying cells A1-A3 to B1 would be done by passing
        start_location="A1", end_location="A3", and to_location="B1".

        The start_location value does not necessarily have to be the top left
        corner of the area to copy, nor does the end_location value have to be
        the bottom right corner of the area; they are simply two corners of
        the area to copy.

        This function works correctly even when the destination area overlaps
        the source area.

        The sheet name matches are case-insensitive; the text must match but
        the case does not have to.

        If to_sheet is None then the cells are being copied to another
        location within the source sheet.

        If any specified sheet name is not found, a KeyError is raised.
        If any cell location is invalid, a ValueError is raised.

        If the target area would extend outside the valid area of the
        spreadsheet (i.e. beyond cell ZZZZ9999), a ValueError is raised, and
        no changes are made to the spreadsheet.'''

        _, shifted_cells, shifted_contents = \
        self._shift_cells_helper(sheet_name, start_location, end_location, \
         to_location, to_sheet  = to_sheet)

        if to_sheet is None:
            to_sheet = sheet_name

        ## Set new contents
        for i, cell in enumerate(shifted_cells):
            self.set_cell_contents(to_sheet, cell, shifted_contents[i], bulk_op = True)

        self._process_update_dict()

    def sort_region(self, sheet_name: str, start_location: str, end_location: str, sort_cols: List[int]):
        '''Sort the specified region of a spreadsheet with a stable sort, using
        the specified columns for the comparison.

        The sheet name match is case-insensitive; the text must match but the
        case does not have to.

        The start_location and end_location specify the corners of an area of
        cells in the sheet to be sorted.  Both corners are included in the
        area being sorted; for example, sorting the region including cells B3
        to J12 would be done by specifying start_location="B3" and
        end_location="J12".

        The start_location value does not necessarily have to be the top left
        corner of the area to sort, nor does the end_location value have to be
        the bottom right corner of the area; they are simply two corners of
        the area to sort.

        The sort_cols argument specifies one or more columns to sort on.  Each
        element in the list is the one-based index of a column in the region,
        with 1 being the leftmost column in the region.  A column's index in
        this list may be positive to sort in ascending order, or negative to
        sort in descending order.  For example, to sort the region B3..J12 on
        the first two columns, but with the second column in descending order,
        one would specify sort_cols=[1, -2].

        The sorting implementation is a stable sort:  if two rows compare as
        "equal" based on the sorting columns, then they will appear in the
        final result in the same order as they are at the start.

        If multiple columns are specified, the behavior is as one would
        expect:  the rows are ordered on the first column indicated in
        sort_cols; when multiple rows have the same value for the first
        column, they are then ordered on the second column indicated in
        sort_cols; and so forth.

        No column may be specified twice in sort_cols; e.g. [1, 2, 1] or
        [2, -2] are both invalid specifications.

        The sort_cols list may not be empty.  No index may be 0, or refer
        beyond the right side of the region to be sorted.

        If the specified sheet name is not found, a KeyError is raised.
        If any cell location is invalid, a ValueError is raised.
        If the sort_cols list is invalid in any way, a ValueError is raised.'''

        # Check validity of sheet name, cell values, and column indices
        if sheet_name.lower() not in self.sheets:
            raise KeyError("Sheet {} not in workbook.".format(sheet_name))
        c1 = get_cell_tuple(start_location)
        c2 = get_cell_tuple(end_location)

        top_left = (min(c1[0], c2[0]), min(c1[1], c2[1]))
        bottom_right = (max(c1[0], c2[0]), max(c1[1], c2[1]))



        # check sort_cols
        for c in sort_cols:
            if type(c) != int:
                raise ValueError("sort_cols should be type List[Int]")
            if abs(c) > bottom_right[1]:
                raise ValueError("sort_cols out of selected range")

        abs_cols = [abs(c) for c in sort_cols]
        if len(abs_cols) != len(set(abs_cols)):
            raise ValueError("sort_cols contains duplicates")

        source_cells = []
        for row in range(top_left[1], bottom_right[1] + 1):
            row_tup = []
            for col in range(top_left[0], bottom_right[0] + 1):
                row_tup.append(get_cell_name((col, row)))
            source_cells.append(row_tup)

        # Get original column and value grids
        c_grid = [[self.get_cell_contents(sheet_name, cell) for cell in row] \
                                                     for row in source_cells]

        v_grid = [[self.get_cell_value(sheet_name, cell) for cell in row] \
                                                     for row in source_cells ]

        # Generate row objects and sort them
        row_objects = []
        for i, row in enumerate(v_grid):
            row_objects.append(rowProxy(i, sort_cols, row))

        sorted_rows = sorted(row_objects)

        # Move rows
        for row_ind, row_obj in enumerate(sorted_rows):
            old_ind = row_obj.row_ind
            row_shift = row_ind - old_ind
            # If the row was not shifted at all, do nothing
            if row_shift == 0:
                continue

            # Generate the row's new contents
            old_contents = c_grid[old_ind]
            new_contents = []
            for cont in old_contents:
                if cont is not None and cont[0] == "=":
                    cont = self._get_formula_shift_cells(cont, (0,row_shift))
                new_contents.append(cont)

            # Go though and set new contents
            row_cells = source_cells[row_ind]
            for col_ind, cell in enumerate(row_cells):
                # Only set contents if new contents is different from what was
                # previously in this location
                if new_contents[col_ind] != c_grid[row_ind][col_ind]:
                    self.set_cell_contents(sheet_name, cell, new_contents[col_ind], bulk_op = True)

        self._process_update_dict()

        ## Process:
        # 1. Generate get grids of values and contents
        # 2. Generate row proxy objects
        # 3. Sort row proxy objects
        # 4. Go though sorted list, get shift of each rows
            # For each cell in row:
                # If is_formula and there is a shift, get new contents
            # set_cell_contents for all non-none cell in row
