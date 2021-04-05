'''Tests for the second project'''
import sheets
import context

# Now we can import other things
import io
import json
import pytest

from sheets import Workbook, CellError, CellErrorType, cell
# pylint: disable=protected-access

def is_error(val, error_type):
    '''Helper function for CellErrors'''
    if isinstance(val, CellError):
        if val.get_type() == error_type:
            return True
    return False

def test_move_sheet():
    '''move sheet basics'''
    workbook = Workbook()
    workbook.new_sheet("s1")
    workbook.new_sheet("s2")
    workbook.move_sheet("s1", 1)
    assert workbook.list_sheets() == ["s2", "s1"]
    workbook.move_sheet("s1", 0)
    assert workbook.list_sheets() == ["s1", "s2"]
    with pytest.raises(KeyError):
        workbook.move_sheet("Africa", 1)
    with pytest.raises(IndexError):
        workbook.move_sheet("s1", 2)
    with pytest.raises(IndexError):
        workbook.move_sheet("s1", -2)

def test_copy_sheet_basic():
    '''copy sheet basics'''
    workbook = Workbook()

    workbook.new_sheet("S")
    workbook.copy_sheet("s")
    assert workbook.list_sheets() == ["S", "S-1"]

def test_copy_sheet_increment():
    '''copy sheet increment'''
    book = Workbook()
    book.new_sheet("S1")
    book.new_sheet("S1-1")

    book.copy_sheet("S1")
    assert book.list_sheets() == ["S1", "S1-1", "S1-2"]

def test_copy_sheet():
    '''copy sheet continued'''
    workbook = Workbook()

    workbook.new_sheet("s")
    workbook.set_cell_contents("s", 'c1', '1')
    workbook.set_cell_contents("s", 'd1', '= c1 + 1')
    workbook.set_cell_contents("s", 'e1', '= e1')
    workbook.copy_sheet("s")
    workbook.copy_sheet("s")
    workbook.copy_sheet("s-1")
    assert workbook.list_sheets() == ["s", "s-1", "s-2", "s-1-1"]
    assert is_error(workbook.get_cell_value("s", 'e1'), CellErrorType.CIRCULAR_REFERENCE)
    assert workbook.get_cell_value("s", 'c1') == 1

    # If I change value in old sheet, new one doesn't respond
    workbook.set_cell_contents("s", 'e1', 'hello')
    assert is_error(workbook.get_cell_value("s-1", 'e1'), CellErrorType.CIRCULAR_REFERENCE)

    # If i set value in new sheet, old one doesn't respond
    workbook.set_cell_contents("s-1", 'c1', 'hello')
    assert workbook.get_cell_value("s", 'c1') == 1

def test_copy_sheet_with_existing_refs():
    '''copy sheet with dependencies'''
    workbook = Workbook()
    workbook.new_sheet("s")
    workbook.new_sheet("s1")

    workbook.set_cell_contents("s", 'A1', '1')
    workbook.set_cell_contents("s1", 'A1', '=\'s-1\'!A1')
    assert is_error(workbook.get_cell_value("s1", 'a1'), CellErrorType.BAD_NAME)

    workbook.copy_sheet("s")
    assert workbook.get_cell_value("s1", 'a1') == 1

def test_rename_formula_new_sheet():
    '''rename a formula'''
    workbook = Workbook()
    workbook.new_sheet("s1")

    assert workbook._get_formula_new_sheet('= 5 + 6 + 1', "s1", "S4") == "=5 + 6 + 1"
    assert workbook._get_formula_new_sheet('= 5 + 6 * 1', "s1", "S4") == "=5 + 6 * 1"
    assert workbook._get_formula_new_sheet('= (5+6) * 1', "s1", "S4") == "=(5 + 6) * 1"
    assert workbook._get_formula_new_sheet('= 5 & "hi"', "s1", "S4") == '=5 & "hi"'

    # More complex formulas
    form = '= ((5+6) & "hi")* -1'
    assert workbook._get_formula_new_sheet( form, "s1", "S4") == '=((5 + 6) & \"hi\") * -1'

    form = "=a1 & \"hello\" & (3 + 4 * 2)"
    assert workbook._get_formula_new_sheet(form, "s1", "S4") == '=a1 & "hello" & (3 + 4 * 2)'

    form = "=-4.3 * (\"hello\" & B5)"
    assert workbook._get_formula_new_sheet(form, "s1", "S4") == '=-4.3 * (\"hello\" & B5)'

    form = "=(5+5)*6*6"
    assert workbook._get_formula_new_sheet(form, "s1", "S4") == '=(5 + 5) * 6 * 6'

    form = "=(5&5)*6*6"
    assert workbook._get_formula_new_sheet(form, "s1", "S4") == '=(5 & 5) * 6 * 6'

    form = "=(5 & 5) + 6 + 6"
    assert workbook._get_formula_new_sheet(form, "s1", "S4") == '=(5 & 5) + 6 + 6'

    form = '=(5 + 5) & "a" & "a"'
    assert workbook._get_formula_new_sheet(form, "s1", "S4") == '=(5 + 5) & "a" & "a"'

    form = '=(5 / 5) & "a" & "a"'
    assert workbook._get_formula_new_sheet(form, "s1", "S4") == '=(5 / 5) & "a" & "a"'

    form = '=5 + "Infinity" '
    assert workbook._get_formula_new_sheet(form, "s1", "S4") == '=5 + "Infinity"'

    # Actually changing the sheet name
    form = "=-4.3 * (\"hello\" & s1!B5)"
    assert workbook._get_formula_new_sheet(form, "s1", "S4") == '=-4.3 * (\"hello\" & S4!B5)'
    assert workbook._get_formula_new_sheet('= s1!a1', "s1", "S4") == '=S4!a1'
    assert workbook._get_formula_new_sheet('= S1!a1', "s1", "S4") == '=S4!a1'
    assert workbook._get_formula_new_sheet('= non!a1*2', "s1", "S4") == '=non!a1 * 2'

    # If the formula cannot be parsed, don't update it
    assert workbook._get_formula_new_sheet('= s1!a1*2#', "s1", "S4") == '= s1!a1*2#'

    #Absolute references
    assert workbook._get_formula_new_sheet('= s1!$a$1 * 2', "s1", "S4") == '=S4!$a$1 * 2'
    assert workbook._get_formula_new_sheet('= a$1 * 2', "s1", "S4") == '=a$1 * 2'

    # Rename with single quotes
    assert workbook._get_formula_new_sheet('= s1!a1', "s1", " new") == '=\' new\'!a1'
    assert workbook._get_formula_new_sheet('= s1!a1', "s1", "new*") == '=\'new*\'!a1'
    assert workbook._get_formula_new_sheet('= s1!a1', "s1", "5new") == '=\'5new\'!a1'
    assert workbook._get_formula_new_sheet('= \'sheet1\'!a1', "s1", "S4") == '=sheet1!a1'

def test_rename_sheet_basic():
    '''rename sheet basics'''
    workbook = Workbook()
    workbook.new_sheet("S1")
    workbook.new_sheet("S2")

    workbook.set_cell_contents("S2", 'c1', '5')
    workbook.set_cell_contents("S2", 'd1', '= c1 + 1')
    workbook.set_cell_contents("S2", 'e1', '= S2!c1 + 1')

    workbook.set_cell_contents("S1", 'a1', '= S2!c1 + 1') #ref 1 cell in rename
    workbook.set_cell_contents("S1", 'a2', '= s2!c1 + S2!d1') #ref >1 cell in rename
    #cell in rename sheet ref cell in other sheet
    workbook.set_cell_contents("S2", 'a1', '= {}!a1 + 1'.format("S1"))

    workbook.rename_sheet("S2", "renamed")
    assert workbook.get_cell_value("S1", "a1") == 6
    assert workbook.get_cell_value("S1", "a2") == 11

    assert workbook.get_cell_value("renamed", "a1") == 7
    assert workbook.get_cell_value("renamed", "d1") == 6
    assert workbook.get_cell_value("renamed", "d1") == 6

    assert workbook.list_sheets() == ["S1", "renamed"]

def test_rename_sheet_more():
    '''rename tests continued'''
    workbook = Workbook()
    workbook.new_sheet("S1")
    workbook.new_sheet("S2")

    workbook.set_cell_contents("S2", 'c1', '5')

    workbook.set_cell_contents("S1", 'a1', '= renamed!c1 + 1')
    assert is_error(workbook.get_cell_value("S1", "A1"), CellErrorType.BAD_NAME)


    workbook.rename_sheet("S2", "renamed")
    assert workbook.get_cell_value("S1", "a1") == 6


    assert workbook.list_sheets() == ["S1", "renamed"]

def test_rename_sheet_parse_error_prop():
    '''error propogation with rename'''
    workbook = Workbook()
    workbook.new_sheet("S1")
    workbook.new_sheet("S2")

    workbook.set_cell_contents("S2", 'd1', '= c1*# + 1')
    workbook.set_cell_contents("S1", 'a1', '=s2!d1')

    workbook.rename_sheet("s2", "renamed")
    assert is_error(workbook.get_cell_value("renamed", "d1"), CellErrorType.PARSE_ERROR)
    assert is_error(workbook.get_cell_value("S1", "a1"), CellErrorType.PARSE_ERROR)

def test_absolute_cell_ref():
    '''different cell references'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")

    workbook.set_cell_contents(name, 'a1', '= $z$1')
    assert workbook.get_cell_value(name, "a1") == 0

    workbook.set_cell_contents(name, 'a1', '= z$1')
    assert workbook.get_cell_value(name, "a1") == 0

    workbook.set_cell_contents(name, 'a1', '= $z1')
    assert workbook.get_cell_value(name, "a1") == 0

    workbook.set_cell_contents(name, 'a1', '= $Z1')
    assert workbook.get_cell_value(name, "a1") == 0

    workbook.set_cell_contents(name, 'a1', '= non!$Z$1')
    assert is_error(workbook.get_cell_value(name, "a1"), CellErrorType.BAD_NAME)

def test_move_sheet_bad_inputs():
    '''move bad inputs'''
    workbook = Workbook()
    (_index, _name) = workbook.new_sheet("sheet1")
    with pytest.raises(ValueError):
        workbook.move_cells("sheet1","Z01", "a1", "b1")
    with pytest.raises(ValueError):
        workbook.move_cells("sheet1","a1", "xxxxx1", "b1")
    with pytest.raises(ValueError):
        workbook.move_cells("sheet1","a1", "b1", "x1$")
    with pytest.raises(KeyError):
        workbook.move_cells("no sheet","a1", "b1", "a2")
    with pytest.raises(KeyError):
        workbook.move_cells("sheet1","a1", "b1", "a2", "no_sheet")

def test_move_cells_non_overlap():
    ''' Non-overlapping move, same sheet'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")
    workbook.set_cell_contents(name, "a1", "5")
    workbook.set_cell_contents(name, "a2", "=A1")
    workbook.set_cell_contents(name, "a3", "=$A1")
    workbook.set_cell_contents(name, "a4", "=A$1")
    workbook.set_cell_contents(name, "a5", "=$A$1")

    workbook.set_cell_contents(name, "a10", "=A1")

    workbook.move_cells(name, "a1", "a5", "b2")

    assert workbook.get_cell_contents(name, "b2") == "5"
    assert workbook.get_cell_contents(name, "b3") == "=B2"
    assert workbook.get_cell_contents(name, "b4") == "=$A2"
    assert workbook.get_cell_contents(name, "b5") == "=B$1"
    assert workbook.get_cell_contents(name, "b6") == "=$A$1"

    assert workbook.get_cell_value(name, "a1") is None
    assert workbook.get_cell_value(name, "a2") is None
    assert workbook.get_cell_value(name, "a3") is None
    assert workbook.get_cell_value(name, "a4") is None
    assert workbook.get_cell_value(name, "a5") is None
    assert workbook.get_cell_value(name, "a10") == 0

    assert workbook.get_cell_value(name, "b2") == 5
    assert workbook.get_cell_value(name, "b3") == 5
    assert workbook.get_cell_value(name, "b4") == 0
    assert workbook.get_cell_value(name, "b5") == 0
    assert workbook.get_cell_value(name, "b6") == 0

def test_move_cells_overlap():
    '''Overlapping move, same sheet'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")
    workbook.set_cell_contents(name, "a1", "5")
    workbook.set_cell_contents(name, "a2", "=A1")

    workbook.move_cells(name, "a1", "b2", "b2")

    assert workbook.get_cell_contents(name, "b2") == "5"
    assert workbook.get_cell_contents(name, "b3") == "=B2"
    assert workbook.get_cell_contents(name, "c2") is None
    assert workbook.get_cell_contents(name, "c3") is None


    assert workbook.get_cell_value(name, "a1") is None
    assert workbook.get_cell_value(name, "a2") is None
    assert workbook.get_cell_value(name, "a1") is None

    assert workbook.get_cell_value(name, "b2") == 5
    assert workbook.get_cell_value(name, "b3") == 5
    assert workbook.get_cell_value(name, "c2") is None
    assert workbook.get_cell_value(name, "c3") is None

def test_move_cells_oder_swap_overlap():
    ''' switch order of inputs'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")
    workbook.set_cell_contents(name, "a1", "5")
    workbook.set_cell_contents(name, "a2", "=A1")

    workbook.move_cells(name, "a2", "b1", "b2")

    assert workbook.get_cell_contents(name, "b2") == "5"
    assert workbook.get_cell_contents(name, "b3") == "=B2"
    assert workbook.get_cell_contents(name, "c2") is None
    assert workbook.get_cell_contents(name, "c3") is None

    assert workbook.get_cell_value(name, "a1") is None
    assert workbook.get_cell_value(name, "a2") is None
    assert workbook.get_cell_value(name, "a1") is None

    assert workbook.get_cell_value(name, "b2") == 5
    assert workbook.get_cell_value(name, "b3") == 5
    assert workbook.get_cell_value(name, "c2") is None
    assert workbook.get_cell_value(name, "c3") is None


def test_move_cells_oob_ref_same_sheet():
    '''Reference will be out of bounds after move'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")
    workbook.set_cell_contents(name, "a2", "=a1")
    workbook.set_cell_contents(name, "a3", "=a2")
    workbook.move_cells(name, "a2", "a3", "a1")

    assert workbook.get_cell_value(name, "a3") is None

    assert workbook.get_cell_contents(name, "a1") == '="#REF!"'
    assert workbook.get_cell_value(name, "a1") == "#REF!"
    assert workbook.get_cell_contents(name, "a2") == '=A1'
    assert workbook.get_cell_value(name, "a2") == "#REF!"

def test_move_cells_oob_ref_diff_sheet():
    ''' Reference will be out of bounds after move'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")
    (_index, name2) = workbook.new_sheet("sheet2")
    workbook.set_cell_contents(name, "a2", "=a1")
    workbook.set_cell_contents(name, "a3", "=a2")
    workbook.move_cells(name, "a2", "a3", "a1", name2)

    assert workbook.get_cell_value(name, "a3") is None

    assert workbook.get_cell_contents(name2, "a1") == '="#REF!"'
    assert workbook.get_cell_value(name2, "a1") == "#REF!"
    assert workbook.get_cell_contents(name2, "a2") == '=A1'
    assert workbook.get_cell_value(name2, "a2") == "#REF!"


changed = set([])
def on_cells_changed(_workbook, changed_cells):
    '''
    This function gets called when cells change in the workbook that the
    function was registered on.  The changed_cells argument is an iterable
    of tuples; each tuple is of the form (sheet_name, cell_location). It simply
    add the liustof changed_cells to the changed global set.
    '''
    global changed
    changed |= set(changed_cells)

def test_notify_cell_update_one_cell():
    '''notify simple update'''
    global changed
    workbook = Workbook()
    (_index, _name) = workbook.new_sheet("Sheet1")
    workbook.notify_cells_changed(on_cells_changed)

    changed = set([])
    workbook.set_cell_contents("Sheet1", "A1", '=1/0')
    cells = {("Sheet1", "A1")}
    assert cells.issubset(changed)

def test_notify_cell_update_children():
    '''notify with children'''
    global changed
    workbook = Workbook()
    (_index, _name) = workbook.new_sheet("Sheet1")
    workbook.notify_cells_changed(on_cells_changed)

    workbook.set_cell_contents("Sheet1", "A1", '=1/0')
    workbook.set_cell_contents("Sheet1", "A2", '=A1')

    changed = set([])
    workbook.set_cell_contents("Sheet1", "A1", None)
    cells = {("Sheet1", "A1"), ("Sheet1", "A2")}
    assert cells.issubset(changed)

def test_notify_cell_update_circ_dep():
    '''notify circular dependency'''
    global changed
    workbook = Workbook()
    (_index, _name) = workbook.new_sheet("Sheet1")
    workbook.notify_cells_changed(on_cells_changed)

    workbook.set_cell_contents("Sheet1", "A1", '=A3')
    workbook.set_cell_contents("Sheet1", "A2", '=A1')
    workbook.set_cell_contents("Sheet1", "A3", '=A1')

    changed = set([])
    workbook.set_cell_contents("Sheet1", "A1", None)
    cells = {("Sheet1", "A1"), ("Sheet1", "A2"), ("Sheet1", "A3")}
    assert cells.issubset(changed)

def test_notify_cell_update_del_sheet():
    '''notify delete sheet'''
    global changed
    workbook = Workbook()
    (_index, _name) = workbook.new_sheet("Sheet1")
    (_index, _name) = workbook.new_sheet("Sheet2")
    workbook.notify_cells_changed(on_cells_changed)

    workbook.set_cell_contents("Sheet1", "A1", '=1/0')
    workbook.set_cell_contents("Sheet2", "A2", '=sheet1!A1')

    changed = set([])
    workbook.del_sheet("Sheet1")
    cells = {("Sheet2", "A2")}
    assert cells == changed

def test_notify_cell_update_new_sheet_existing_refs():
    '''notify new sheet with dependencies'''
    global changed
    workbook = Workbook()
    (_index, _name) = workbook.new_sheet("Sheet1")
    workbook.notify_cells_changed(on_cells_changed)
    workbook.set_cell_contents("Sheet1", "A1", '=1/0')
    # Cell referenceing non-existent sheet
    workbook.set_cell_contents("Sheet1", "A2", '=sheet2!A1')

    changed = set([])
    (_index, _name) = workbook.new_sheet("Sheet2")
    cells = {("Sheet1", "A2")}
    assert cells == changed

def test_notify_cell_update_move_cells_basic():
    '''notify cell basics'''
    global changed
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("Sheet1")
    workbook.notify_cells_changed(on_cells_changed)
    workbook.set_cell_contents(name, "a1", "5")
    workbook.set_cell_contents(name, "a2", "=A1")

    changed = set([])
    workbook.move_cells(name, "a1", "a2", "b1")
    cells = {("Sheet1", "A1"), ("Sheet1", "A2"), ("Sheet1", "B1"), ("Sheet1", "B2")}
    assert cells.issubset(changed)

def test_notify_cell_update_move_cells_with_dep():
    '''notify move cells with dependencies'''
    global changed
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("Sheet1")
    workbook.notify_cells_changed(on_cells_changed)
    workbook.set_cell_contents(name, "a1", "5")
    workbook.set_cell_contents(name, "a2", "=A1")
    workbook.set_cell_contents(name, "a5", "=A1")

    changed = set([])
    workbook.move_cells(name, "a1", "a2", "b1")
    cells = {("Sheet1", "A1"), ("Sheet1", "A2"),
            ("Sheet1", "B1"), ("Sheet1", "B2"),
            ("Sheet1", "A5")}
    assert cells.issubset(changed)

def test_notify_cell_update_move_cells_overlap():
    '''notify cell move with overlap'''
    global changed
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("Sheet1")
    workbook.notify_cells_changed(on_cells_changed)
    workbook.set_cell_contents(name, "a1", "5")
    workbook.set_cell_contents(name, "a2", "=A1")

    changed = set([])
    workbook.move_cells(name, "a1", "a2", "a2")
    cells = {("Sheet1", "A1"),("Sheet1", "A3")}
    assert cells.issubset(changed)

def test_notify_cell_update_rename_sheet():
    '''notify rename sheet'''
    global changed
    workbook = Workbook()
    (_index, _name) = workbook.new_sheet("Sheet1")
    (_index, _name) = workbook.new_sheet("Sheet2")

    workbook.notify_cells_changed(on_cells_changed)
    workbook.set_cell_contents("Sheet1", "a1", "5")
    workbook.set_cell_contents("Sheet1", "a2", "=A1")
    workbook.set_cell_contents("Sheet2", "a2", "=Sheet1!A1")

    changed = set([])
    workbook.rename_sheet("sheet1", "renamed")
    cells = set([])
    assert cells == changed

def test_notify_cell_update_copy_sheet():
    '''notify on copy sheet'''
    global changed
    workbook = Workbook()
    (_index, _name) = workbook.new_sheet("Sheet1")

    workbook.notify_cells_changed(on_cells_changed)
    workbook.set_cell_contents("Sheet1", "a1", "5")
    workbook.set_cell_contents("Sheet1", "a2", "=A1")

    changed = set([])
    (_index, _name1) = workbook.copy_sheet("sheet1")
    cells = {("Sheet1-1", "A1"),("Sheet1-1", "A2")}
    assert cells == changed

def test_notify_cell_update_copy_cells_basic():
    '''notify basics'''
    global changed
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("Sheet1")
    workbook.notify_cells_changed(on_cells_changed)
    workbook.set_cell_contents(name, "a1", "5")
    workbook.set_cell_contents(name, "a2", "=A1")

    changed = set([])
    workbook.copy_cells(name, "a1", "a2", "b1")
    cells = {("Sheet1", "B1"), ("Sheet1", "B2")}
    assert cells == changed

def test_notify_cell_update_copy_cells_with_dep():
    '''update with dependencies'''
    global changed
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("Sheet1")
    workbook.notify_cells_changed(on_cells_changed)
    workbook.set_cell_contents(name, "a1", "5")
    workbook.set_cell_contents(name, "a2", "=A1")
    workbook.set_cell_contents(name, "a5", "=A1")

    changed = set([])
    workbook.copy_cells(name, "a1", "a2", "b1")
    cells = {("Sheet1", "B1"), ("Sheet1", "B2")}
    assert cells==changed

def test_notify_cell_update_copy_cells_overlap():
    '''notify on cell overlap'''
    global changed
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("Sheet1")
    workbook.notify_cells_changed(on_cells_changed)
    workbook.set_cell_contents(name, "a1", "5")
    workbook.set_cell_contents(name, "a2", "=A1")

    changed = set([])
    workbook.copy_cells(name, "a1", "a2", "a2")
    cells = {("Sheet1", "A3")}
    assert cells == changed

def test_save_notebook_basic():
    '''save basics'''
    with io.StringIO() as filep:
        workbook = Workbook()
        workbook.new_sheet("SheeT1")
        workbook.set_cell_contents("SheeT1", "a1", "5")
        workbook.set_cell_contents("SheeT1", "b6", "10")
        workbook.save_workbook(filep)
        filep.seek(0)
        results = json.load(filep)
        expected = {
            "version":"{}".format(sheets.version), "sheets":[
                {
                    "name":"SheeT1",
                    "cell-contents":{
                        "A1":"5",
                        "B6":"10"
                    }
                }
            ]
        }
        assert results == expected

def test_save_notebook_random_contents():
    '''save random values'''
    with io.StringIO() as filep:
        workbook = Workbook()
        workbook.new_sheet("ShEeT1")
        workbook.set_cell_contents("ShEeT1", "a1", "'1 1 1    ")
        workbook.set_cell_contents("ShEeT1", "b6", "=    10 + a1")
        workbook.save_workbook(filep)
        filep.seek(0)
        results = json.load(filep)
        expected = {
            "version":"{}".format(sheets.version), "sheets":[
                {
                    "name":"ShEeT1",
                    "cell-contents":{
                        "A1":"'1 1 1",
                        "B6":"=    10 + a1"
                    }
                }
            ]
        }
        assert results == expected

def test_save_notebook_delete_cell():
    '''save delete cell'''
    with io.StringIO() as filep:
        workbook = Workbook()
        workbook.new_sheet("ShEeT123")
        workbook.set_cell_contents("ShEeT123", "a1", "=24 + 5")
        workbook.set_cell_contents("ShEeT123", "b6", "=25/0")
        workbook.set_cell_contents("ShEeT123", "a1", "")
        workbook.save_workbook(filep)
        filep.seek(0)
        results = json.load(filep)
        expected = {
            "version":"{}".format(sheets.version), "sheets":[
                {
                    "name":"ShEeT123",
                    "cell-contents":{
                        "B6":"=25/0"
                    }
                }
            ]
        }
        assert results == expected

def test_save_notebook_multiple_sheet():
    '''save multiple sheets'''
    with io.StringIO() as filep:
        workbook = Workbook()
        workbook.new_sheet("ShEeT123")
        workbook.set_cell_contents("ShEeT123", "a1", "=24 + 5")
        workbook.set_cell_contents("ShEeT123", "b6", "=25/0")
        workbook.set_cell_contents("ShEeT123", "a1", "")
        workbook.new_sheet("S")
        workbook.save_workbook(filep)
        filep.seek(0)
        results = json.load(filep)
        expected = {
            "version":"{}".format(sheets.version), "sheets":[
                {
                    "name":"ShEeT123",
                    "cell-contents":{
                        "B6":"=25/0"
                    }
                },
                {
                    "name":"S",
                    "cell-contents":{
                    }
                }
            ]
        }
        assert results == expected

def test_save_notebook_delete_sheet():
    '''save delete sheet first'''
    with io.StringIO() as filep:
        workbook = Workbook()
        (_index, name) = workbook.new_sheet("ShEeT123")
        workbook.set_cell_contents(name, "a1", "=24 + 5")
        workbook.set_cell_contents(name, "b6", "=25/0")
        workbook.set_cell_contents(name, "a1", "")
        (_index1, name1) = workbook.new_sheet("S")
        workbook.set_cell_contents(name1, "ba25", "'stinky")
        workbook.del_sheet(name)
        workbook.save_workbook(filep)
        filep.seek(0)
        results = json.load(filep)
        expected = {
            "version":"{}".format(sheets.version), "sheets":[
                {
                    "name":"S",
                    "cell-contents":{
                        "BA25":"'stinky"
                    }
                }
            ]
        }
        assert results == expected

def test_save_notebook_preserve_order():
    '''save ordering'''
    with io.StringIO() as filep:
        workbook = Workbook()
        (_index, name) = workbook.new_sheet("ShEeT123")
        workbook.set_cell_contents(name, "a1", "=24 + 5")
        workbook.set_cell_contents(name, "b6", "=25/0")
        (_index1, name1) = workbook.new_sheet("S")
        workbook.set_cell_contents(name1, "ba25", "'stinky")
        (_index2, name2) = workbook.new_sheet("lmao")
        workbook.set_cell_contents(name2, "a5", "=22+5")
        workbook.del_sheet(name1)
        workbook.save_workbook(filep)
        filep.seek(0)
        results = json.load(filep)
        expected = {
            "version":"{}".format(sheets.version), "sheets":[
                {
                    "name":"ShEeT123",
                    "cell-contents":{
                        "A1":"=24 + 5",
                        "B6":"=25/0"
                    }
                },
                {
                    "name":"lmao",
                    "cell-contents":{
                        "A5":"=22+5"
                    }
                }
            ]
        }
        assert results == expected

def test_load_notebook_basic():
    '''load basics'''
    to_load = '{ "version":"1.2", "sheets":[{"name":"Sheet1",\
        "cell-contents":{"A1":"24"}}]}'

    with io.StringIO(to_load) as filep:
        workbook = Workbook.load_workbook(filep)

        assert workbook.get_cell_value("Sheet1", "a1") == 24

def test_load_notebook_multiple_sheets():
    '''load multiple sheets'''
    to_load = '{ "version":"1.2", "sheets":[{"name":"Sheet1",\
        "cell-contents":{"A1":"24"}},{"name":"Sheet2",\
        "cell-contents":{"A5":"=Sheet1!A1 + 5"}}]}'

    with io.StringIO(to_load) as filep:
        workbook = Workbook.load_workbook(filep)

        assert workbook.get_cell_value("Sheet1", "a1") == 24
        assert workbook.get_cell_value("Sheet2", "a5") == 29

def test_load_notebook_version_errors():
    '''load version erros'''
    to_load = '{"sheets":[{"name":"Sheet1",\
        "cell-contents":{"A1":"24"}},{"name":"Sheet2",\
        "cell-contents":{"A5":"=Sheet1!A1 + 5"}}]}'

    with io.StringIO(to_load) as filep:
        with pytest.raises(KeyError):
            Workbook.load_workbook(filep)

    to_load = '{"version":1.2,"sheets":[{"name":"Sheet1",\
        "cell-contents":{"A1":"24"}},{"name":"Sheet2",\
        "cell-contents":{"A5":"=Sheet1!A1 + 5"}}]}'

    with io.StringIO(to_load) as filep:
        with pytest.raises(TypeError):
            Workbook.load_workbook(filep)

def test_load_notebook_sheets_errors():
    '''load sheet errors'''
    to_load = '{ "version":"1.2"}'

    with io.StringIO(to_load) as filep:
        with pytest.raises(KeyError):
            Workbook.load_workbook(filep)

    to_load = '{"version":1.2,"sheets":{"name":"Sheet1",\
        "cell-contents":{"A1":"24"}}}'

    with io.StringIO(to_load) as filep:
        with pytest.raises(TypeError):
            Workbook.load_workbook(filep)

def test_load_notebook_name_errors():
    '''load name errors'''
    to_load = '{ "version":"1.2", "sheets":[{"name":"Sheet1",\
        "cell-contents":{"A1":"24"}},{\
        "cell-contents":{"A5":"=Sheet1!A1 + 5"}}]}'

    with io.StringIO(to_load) as filep:
        with pytest.raises(KeyError):
            Workbook.load_workbook(filep)

    to_load = '{ "version":"1.2", "sheets":[{"name":"Sheet1",\
        "cell-contents":{"A1":"24"}},{"name":1,\
        "cell-contents":{"A5":"=Sheet1!A1 + 5"}}]}'

    with io.StringIO(to_load) as filep:
        with pytest.raises(TypeError):
            Workbook.load_workbook(filep)

def test_load_notebook_cell_contents_errors():
    '''load cell errors'''
    to_load = '{"version":"1.2", "sheets":[{"name":"Sheet1",\
        "cell-contents":{"A1":"24"}},{"name":"Sheet2"}]}'

    with io.StringIO(to_load) as filep:
        with pytest.raises(KeyError):
            Workbook.load_workbook(filep)

    to_load = '{ "version":"1.2", "sheets":[{"name":"Sheet1",\
        "cell-contents":{"A1":"24"}},{"name":1,\
        "cell-contents":10}]}'

    with io.StringIO(to_load) as filep:
        with pytest.raises(TypeError):
            Workbook.load_workbook(filep)

def test_load_notebook_cell_contents_location_errors():
    '''load location errors'''
    to_load = '{ "version":"1.2", "sheets":[{"name":"Sheet1",\
        "cell-contents":{"A1":24}},{"name":"Sheet2",\
        "cell-contents":{"A5":"=Sheet1!A1 + 5"}}]}'

    with io.StringIO(to_load) as filep:
        with pytest.raises(TypeError):
            Workbook.load_workbook(filep)

    to_load = '{ "version":"1.2", "sheets":[{"name":"Sheet1",\
        "cell-contents":{"A1":"24"}},{"name":"Sheet2",\
        "cell-contents":{"5":35}}]}'

    with io.StringIO(to_load) as filep:
        with pytest.raises(TypeError):
            Workbook.load_workbook(filep)

def test_copy_cells_non_overlap():
    '''Non-overlapping move, same sheet'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")
    workbook.set_cell_contents(name, "a1", "5")
    workbook.set_cell_contents(name, "a2", "=A1")
    workbook.set_cell_contents(name, "a3", "=$A1")
    workbook.set_cell_contents(name, "a4", "=A$1")
    workbook.set_cell_contents(name, "a5", "=$A$1")

    workbook.set_cell_contents(name, "a10", "=A1")

    workbook.copy_cells(name, "a1", "a5", "b2")

    assert workbook.get_cell_contents(name, "b2") == "5"
    assert workbook.get_cell_contents(name, "b3") == "=B2"
    assert workbook.get_cell_contents(name, "b4") == "=$A2"
    assert workbook.get_cell_contents(name, "b5") == "=B$1"
    assert workbook.get_cell_contents(name, "b6") == "=$A$1"

    assert workbook.get_cell_value(name, "a1") == 5
    assert workbook.get_cell_value(name, "a2") == 5
    assert workbook.get_cell_value(name, "a3") == 5
    assert workbook.get_cell_value(name, "a4") == 5
    assert workbook.get_cell_value(name, "a5") == 5
    assert workbook.get_cell_value(name, "a10") == 5

    assert workbook.get_cell_value(name, "b2") == 5
    assert workbook.get_cell_value(name, "b3") == 5
    assert workbook.get_cell_value(name, "b4") == 5
    assert workbook.get_cell_value(name, "b5") == 0
    assert workbook.get_cell_value(name, "b6") == 5


def test_copy_cells_overlap():
    ''' Overlapping move, same sheet'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")
    workbook.set_cell_contents(name, "a1", "5")
    workbook.set_cell_contents(name, "a2", "=A1")

    workbook.copy_cells(name, "a1", "b2", "b2")

    assert workbook.get_cell_contents(name, "b2") == "5"
    assert workbook.get_cell_contents(name, "b3") == "=B2"
    assert workbook.get_cell_contents(name, "c2") is None
    assert workbook.get_cell_contents(name, "c3") is None


    assert workbook.get_cell_value(name, "a1") == 5
    assert workbook.get_cell_value(name, "a2") == 5

    assert workbook.get_cell_value(name, "b2") == 5
    assert workbook.get_cell_value(name, "b3") == 5
    assert workbook.get_cell_value(name, "c2") is None
    assert workbook.get_cell_value(name, "c3") is None


def test_copy_cells_oder_swap_overlap():
    ''' switch order of inputs'''
    workbook = Workbook()
    workbook.new_sheet("sheet1")
    workbook.set_cell_contents("sheet1", "a1", "5")
    workbook.set_cell_contents("sheet1", "a2", "=A1")

    workbook.copy_cells("sheet1", "a2", "b1", "b2")

    assert workbook.get_cell_contents("sheet1", "b2") == "5"
    assert workbook.get_cell_contents("sheet1", "b3") == "=B2"
    assert workbook.get_cell_contents("sheet1", "c2") is None
    assert workbook.get_cell_contents("sheet1", "c3") is None


    assert workbook.get_cell_value("sheet1", "a1") == 5
    assert workbook.get_cell_value("sheet1", "a2") == 5

    assert workbook.get_cell_value("sheet1", "b2") == 5
    assert workbook.get_cell_value("sheet1", "b3") == 5
    assert workbook.get_cell_value("sheet1", "c2") is None
    assert workbook.get_cell_value("sheet1", "c3") is None


def test_copy_cells_oob_ref_same_sheet():
    ''' Reference will be out of bounds after move'''
    workbook = Workbook()
    workbook.new_sheet("sheet1")
    workbook.set_cell_contents("sheet1", "a2", "=a1")
    workbook.set_cell_contents("sheet1", "a3", "=a2")
    workbook.copy_cells("sheet1", "a2", "a3", "a1")

    assert workbook.get_cell_value("sheet1", "a3") == "#REF!"
    assert workbook.get_cell_contents("sheet1", "a3") == '=a2'

    assert workbook.get_cell_contents("sheet1", "a1") == '="#REF!"'
    assert workbook.get_cell_value("sheet1", "a1") == "#REF!"
    assert workbook.get_cell_contents("sheet1", "a2") == '=A1'
    assert workbook.get_cell_value("sheet1", "a2") == "#REF!"

def test_copy_cells_oob_ref_diff_sheet():
    '''Reference will be out of bounds after move'''
    workbook = Workbook()
    workbook.new_sheet("sheet1")
    workbook.new_sheet("sheet2")
    workbook.set_cell_contents("sheet1", "a2", "=a1")
    workbook.set_cell_contents("sheet1", "a3", "=a2")
    workbook.copy_cells("sheet1", "a2", "a3", "a1", "sheet2")

    assert workbook.get_cell_value("sheet1", "a3") == 0

    assert workbook.get_cell_contents("sheet2", "a1") == '="#REF!"'
    assert workbook.get_cell_value("sheet2", "a1") == "#REF!"
    assert workbook.get_cell_contents("sheet2", "a2") == '=A1'
    assert workbook.get_cell_value("sheet2", "a2") == "#REF!"
