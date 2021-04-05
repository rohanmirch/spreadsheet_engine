'''Tests for project 3'''
import context

# Now we can import other things
import pytest
from sheets import Workbook, CellError, CellErrorType
import sheets
# pylint: disable=protected-access

def is_error(val, error_type):
    '''checks if error'''
    if isinstance(val, CellError):
        if val.get_type() == error_type:
            return True
    return False


def test_update_formula_with_bool():
    '''Test formulas to bools'''
    workbook = Workbook()
    (_index, _name) = workbook.new_sheet("s1")

    assert workbook._get_formula_new_sheet('= 5 < 6 + 1', "s1", "S4") == "=5 < 6 + 1"
    assert workbook._get_formula_new_sheet('= 5<>6 + A1', "s1", "S4") == "=5 <> 6 + A1"

    assert workbook._get_formula_new_sheet('= A2 = B2 & " type"', "s1", "S4") == \
        '=A2 = B2 & " type"'

    assert workbook._get_formula_new_sheet('= (5=6) * 1', "s1", "S4") == "=(5 = 6) * 1"

    assert workbook._get_formula_new_sheet('= (5=6) + 1', "s1", "S4") == "=(5 = 6) + 1"

    assert workbook._get_formula_new_sheet('= (5=6) & "hi"', "s1", "S4") == '=(5 = 6) & "hi"'

    assert workbook._get_formula_new_sheet('= 1 + (5 != 6)', "s1", "S4") == "=1 + (5 != 6)"

def test_update_formula_with_func():
    '''Test made up functions'''
    workbook = Workbook()
    (_index, _name) = workbook.new_sheet("s1")

    assert workbook._get_formula_new_sheet('= FUNC()', "s1", "S4") == "=FUNC()"
    assert workbook._get_formula_new_sheet('= FUNC() + 5', "s1", "S4") == "=FUNC() + 5"
    assert workbook._get_formula_new_sheet('= FUNC(1)', "s1", "S4") == '=FUNC(1)'
    assert workbook._get_formula_new_sheet('= FUNC(A1)', "s1", "S4") == "=FUNC(A1)"
    assert workbook._get_formula_new_sheet('= FUNC(True)', "s1", "S4") == "=FUNC(True)"
    assert workbook._get_formula_new_sheet('= FUNC(1, 1)', "s1", "S4") == "=FUNC(1, 1)"
    assert workbook._get_formula_new_sheet('= FUNC(FUNC(1, 1))', "s1", "S4") == "=FUNC(FUNC(1, 1))"
    assert workbook._get_formula_new_sheet('= FUNC(FUNC())', "s1", "S4") == "=FUNC(FUNC())"
    assert workbook._get_formula_new_sheet('= FUNC(FUNC(True))', "s1", "S4") == "=FUNC(FUNC(True))"

    assert workbook._get_formula_new_sheet('= FUNC(FUNC(5), FUNC(5))', "s1", "S4") == \
        "=FUNC(FUNC(5), FUNC(5))"
    assert workbook._get_formula_new_sheet('= FUNC(FUNC(5) > FUNC(5))', "s1", "S4") == \
        "=FUNC(FUNC(5) > FUNC(5))"

def test_boolean_literals():
    '''Test booleans work'''
    workbook = Workbook()
    workbook.new_sheet()
    workbook.set_cell_contents('Sheet1', 'A1', 'true')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A2', '=FALSE')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A2')

def test_equals_operator():
    '''Test equals operator'''
    workbook = Workbook()
    workbook.new_sheet()
    workbook.set_cell_contents('Sheet1', 'A1', '=true = false')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A2', '=1 == 1.0')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '="BLUE" = "blue"')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '= 12 == "12"')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', "'booflol")
    workbook.set_cell_contents('Sheet1', 'B2', "'boof")
    workbook.set_cell_contents('Sheet1', 'A3', '=A2 = B2 & "lol"')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A3'), bool)
    assert workbook.get_cell_value('Sheet1', 'A3')

def test_empty_operand():
    '''Test empty inputs'''
    workbook = Workbook()
    workbook.new_sheet()
    workbook.set_cell_contents('Sheet1', 'A1', '=FALSE = B2')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A2', '=b2 == 0')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A3', '="" = B2')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A3'), bool)
    assert workbook.get_cell_value('Sheet1', 'A3')

    workbook.set_cell_contents('Sheet1', 'A4', '= A10 = B2')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A4'), bool)
    assert workbook.get_cell_value('Sheet1', 'A4')

    workbook.set_cell_contents('Sheet1', 'A5', '= A11 > B4')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A5'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A5')

def test_nequals_operator():
    '''Test not equals operator'''
    workbook = Workbook()
    workbook.new_sheet()
    workbook.set_cell_contents('Sheet1', 'A1', '=true != false')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A2', '=1 <> 1.0')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '="BLUE" <> "blue"')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '= 12 != "12"')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '= FALSE != "12"')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '= 12 != true')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', "'booflol")
    workbook.set_cell_contents('Sheet1', 'B2', "'boof")
    workbook.set_cell_contents('Sheet1', 'A3', '=A2 <> B2 & "lol"')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A3'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A3')

def test_greater_than_operator():
    '''Test greater than operator'''
    workbook = Workbook()
    workbook.new_sheet()
    workbook.set_cell_contents('Sheet1', 'A1', '=9>5')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A2', '="BLUE" > "blue"')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '=FALSE > "blue"')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '=FALSE > 12')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '="BLUE" > 525.13')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '="12" > 12')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '="TRUE" > FALSE')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A2')

def test_less_than_operator():
    '''Test less than operator'''
    workbook = Workbook()
    workbook.new_sheet()
    workbook.set_cell_contents('Sheet1', 'A2', '= "A" < "["')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '= "a" < "["')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '= B10 < "["')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '= B10 < 10')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '= False < True')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

def test_greater_or_equal_operator():
    '''Test greater than or equal to operator'''
    workbook = Workbook()
    workbook.new_sheet()
    workbook.set_cell_contents('Sheet1', 'A1', '=9>=5')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A2', '="BLUE" >= "blue"')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '=FALSE >="blue"')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '=12 >= 12')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '=12 >= 525.13')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '="13" >= "12"')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '="TRUE" >= FALSE')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A2')

def test_less_or_equal_operator():
    '''Test less than or equal to operator'''
    workbook = Workbook()
    workbook.new_sheet()
    workbook.set_cell_contents('Sheet1', 'A1', '=9<=5')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A2', '="BLUE" <= "blue"')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '=FALSE <= "blue"')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '=12 <= 12')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '=12 <= 525.13')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '="13" <= "12"')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A2')

    workbook.set_cell_contents('Sheet1', 'A2', '="TRUE" <= FALSE')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A2'), bool)
    assert workbook.get_cell_value('Sheet1', 'A2')

def test_comparison_precedence():
    '''Test precedence of types in operators'''
    workbook = Workbook()
    workbook.new_sheet()
    workbook.set_cell_contents('Sheet1', 'A1', '=9<=5   + 10')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '="lol" & "pop" == "lolpop"')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '="sheck" <> "sheck" & "wes"')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

def test_function_failures():
    '''Test function failure'''
    workbook = Workbook()
    workbook.new_sheet()
    workbook.set_cell_contents('Sheet1', 'A1', '=BOOF(1,2)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.BAD_NAME)

    workbook.set_cell_contents('Sheet1', 'A1', '=NOT(1,2)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=NOT()')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

def test_conversion_to_boolean():
    '''Test converting to booleans for functions'''
    workbook = Workbook()
    workbook.new_sheet()

    workbook.set_cell_contents('Sheet1', 'A1', '=AND("false")')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=AND("true")')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=AND("notaboolean")')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=AND(-12041.1213014)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=AND(500)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=AND(A2, true)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=AND(0)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=AND(true,true,102,true,"false")')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=AND(-120,true,102,true,"true")')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

def test_AND_function():
    '''Test AND function'''
    workbook = Workbook()
    workbook.new_sheet()
    workbook.set_cell_contents('Sheet1', 'A1', '=AND()')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'B1', '=1/0')
    workbook.set_cell_contents('Sheet1', 'A1', '=AND(b1, B1)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=AND(false)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=AND(true)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=AND(true,true,true,true)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=AND(true,true,true,true,false)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

def test_OR_function():
    '''Test OR function'''
    workbook = Workbook()
    workbook.new_sheet()
    workbook.set_cell_contents('Sheet1', 'A1', '=OR()')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'B1', '=1/0')
    workbook.set_cell_contents('Sheet1', 'A1', '=OR(b1, b1)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=OR(false)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=OR(true)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=OR(false, False, falsE, FaLsE, fAlSe, true)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=OR(false, False, falsE, FaLsE, fAlSe)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=OR(102, 0, "false")')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

def test_NOT_function():
    '''Test NOT function'''
    workbook = Workbook()
    workbook.new_sheet()
    workbook.set_cell_contents('Sheet1', 'A1', '=NOT()')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=NOT(true, true)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'B1', '=1/0')
    workbook.set_cell_contents('Sheet1', 'A1', '=NOT(b1)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=NOT(false)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=NOT(true)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=NOT("true")')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=NOT("false")')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=NOT(12)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=NOT(0)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')


def test_XOR_function():
    '''Test XOR function'''
    workbook = Workbook()
    workbook.new_sheet()
    workbook.set_cell_contents('Sheet1', 'A1', '=NOT()')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=NOT(true, true, true)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=XOR(false, false)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=XOR(true, false)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=XOR(false, true)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=XOR(true, true)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=XOR(12, "true")')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

def test_conversion_to_string():
    '''Test conversion to string for functions'''
    workbook = Workbook()
    workbook.new_sheet()

    workbook.set_cell_contents('Sheet1', 'A1', '=EXACT(true, "TRUE")')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=EXACT("TRUE", true)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=EXACT("TruE", true)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=EXACT("FALSE", false)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=EXACT("5.000001", 5.000001)')
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=EXACT("-125.00", -125.00)')
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=EXACT("", B3)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=EXACT("boof","boof")')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

def test_EXACT_function():
    '''Test EXACT function'''
    workbook = Workbook()
    workbook.new_sheet()

    workbook.set_cell_contents('Sheet1', 'A1', '=EXACT()')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=EXACT("boof")')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=EXACT(true, true, true)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=EXACT(b2, c12)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=EXACT("chungus", "CHUNGUS")')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=EXACT("stinky", "stinky")')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=EXACT(15.02, 15.02)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=EXACT(true, true)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=EXACT(true, false)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=EXACT(true, 12)')
    assert isinstance(workbook.get_cell_value('Sheet1', 'A1'), bool)
    assert not workbook.get_cell_value('Sheet1', 'A1')

def test_IF_function():
    '''Test IF function'''
    workbook = Workbook()
    workbook.new_sheet()

    workbook.set_cell_contents('Sheet1', 'A1', '=IF()')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=IF("boof")')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=IF(true, true)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=IF(true, true,true,true)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'B1', '=1/0')
    workbook.set_cell_contents('Sheet1', 'A1', '=IF(B1, true,false)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=IF(b2, 1,0)')
    assert workbook.get_cell_value('Sheet1', 'A1') == 0

    workbook.set_cell_contents('Sheet1', 'B2', 'True')
    workbook.set_cell_contents('Sheet1', 'A1', '=IF(b2, 1,0)')
    assert workbook.get_cell_value('Sheet1', 'A1') == 1

    workbook.set_cell_contents('Sheet1', 'A1', '=IF(true, 1,A1)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.CIRCULAR_REFERENCE)

    workbook.set_cell_contents('Sheet1', 'A1', '=IF(true, 1,0)')
    assert workbook.get_cell_value('Sheet1', 'A1') == 1

    workbook.set_cell_contents('Sheet1', 'A1', '=IF(false, 1,"boof")')
    assert workbook.get_cell_value('Sheet1', 'A1') == "boof"

    workbook.set_cell_contents('Sheet1', 'A1', '=IF("tRUe", true,0)')
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=IF(false, 1,false)')
    assert workbook.get_cell_value('Sheet1', 'A1') is False

    workbook.set_cell_contents('Sheet1', 'A1', '=IF(1, 1,false)')
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=IF(0, 1,false)')
    assert not workbook.get_cell_value('Sheet1', 'A1')

def test_IFERROR_function():
    '''Test IFERROR function'''
    workbook = Workbook()
    workbook.new_sheet()

    workbook.set_cell_contents('Sheet1', 'A1', '=IFERROR()')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=IFERROR(true, true,true,true)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=IFERROR(10/0)')
    assert workbook.get_cell_value('Sheet1', 'A1') == ""

    workbook.set_cell_contents('Sheet1', 'A1', '=IFERROR(1, 0)')
    assert workbook.get_cell_value('Sheet1', 'A1') == 1

    workbook.set_cell_contents('Sheet1', 'B2', "=10/0")
    workbook.set_cell_contents('Sheet1', 'A1', '=IFERROR(b2, 0)')
    assert workbook.get_cell_value('Sheet1', 'A1') == 0

    workbook.set_cell_contents('Sheet1', 'B2', "=B3")
    workbook.set_cell_contents('Sheet1', 'B3', "=B2")
    workbook.set_cell_contents('Sheet1', 'A1', '=IFERROR(b2, "lmao")')
    assert workbook.get_cell_value('Sheet1', 'A1') == "lmao"

    workbook.set_cell_contents('Sheet1', 'B2', "=A1")
    workbook.set_cell_contents('Sheet1', 'A1', '=IFERROR(b2, "nice try")')
    assert workbook.get_cell_value('Sheet1', 'A1') == "nice try"

    workbook.set_cell_contents('Sheet1', 'A1', '=IFERROR(sheet1!a1, "no")')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.CIRCULAR_REFERENCE)

    workbook.set_cell_contents('Sheet1', 'B1', '=IFERROR(sheet1!a1, "no")')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.CIRCULAR_REFERENCE)

def test_conversion_to_number():
    '''Test conversion to number for functions'''
    workbook = Workbook()
    workbook.new_sheet()

    workbook.set_cell_contents('Sheet1', 'A1', '=CHOOSE(false, 20, true)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=CHOOSE(true, 20)')
    assert workbook.get_cell_value('Sheet1', 'A1') == 20

    workbook.set_cell_contents('Sheet1', 'A1', '=CHOOSE(b2, 20, true)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=CHOOSE("2", 20, "true", "sick")')
    assert workbook.get_cell_value('Sheet1', 'A1') == "true"

    workbook.set_cell_contents('Sheet1', 'A1', '=CHOOSE("1-2", 1,2)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

def test_CHOOSE_function():
    '''Test CHOOSE function'''
    workbook = Workbook()
    workbook.new_sheet()

    workbook.set_cell_contents('Sheet1', 'A1', '=CHOOSE()')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=CHOOSE(true)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=CHOOSE(false, 10)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=CHOOSE(-12, 10)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=CHOOSE(300, 10)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=CHOOSE(1, 20)')
    assert workbook.get_cell_value('Sheet1', 'A1') == 20

    workbook.set_cell_contents('Sheet1', 'A1', '=CHOOSE("2", 20, true)')
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=CHOOSE(3, 20, "true", "sick")')
    assert workbook.get_cell_value('Sheet1', 'A1') == "sick"

    workbook.set_cell_contents('Sheet1', 'A1', '=CHOOSE(2, 1,2)')
    assert workbook.get_cell_value('Sheet1', 'A1') == 2

def test_ISBLANK_function():
    '''Test ISBLANK function'''
    workbook = Workbook()
    workbook.new_sheet()

    workbook.set_cell_contents('Sheet1', 'A1', '=ISBLANK("")')
    assert not workbook.get_cell_value('Sheet1', 'a1')

    workbook.set_cell_contents('Sheet1', 'A1', '=ISBLANK(B2)')
    assert workbook.get_cell_value('Sheet1', 'a1')

    workbook.set_cell_contents('Sheet1', 'A1', '=ISBLANK(true, 12)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=ISBLANK()')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=ISBLANK(0)')
    assert not workbook.get_cell_value('Sheet1', 'a1')

    workbook.set_cell_contents('Sheet1', 'A1', '=ISBLANK(false)')
    assert not workbook.get_cell_value('Sheet1', 'a1')

    workbook.set_cell_contents('Sheet1', 'A1', '=ISBLANK(a1)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.CIRCULAR_REFERENCE)

    workbook.set_cell_contents('Sheet1', 'A1', '=ISBLANK(b1)')
    workbook.set_cell_contents('Sheet1', 'b1', '=ISBLANK(a1)')

    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.CIRCULAR_REFERENCE)
    assert is_error(workbook.get_cell_value('Sheet1', 'b1'), CellErrorType.CIRCULAR_REFERENCE)

def test_ISERROR_function():
    '''Test ISERROR function'''
    workbook = Workbook()
    workbook.new_sheet()

    workbook.set_cell_contents('Sheet1', 'A1', '=ISERROR()')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=ISERROR(true, true,true,true)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=ISERROR(10/0)')
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=ISERROR(1)')
    assert not workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'B2', "=10/0")
    workbook.set_cell_contents('Sheet1', 'A1', '=ISERROR(b2)')
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'B2', "=B3")
    workbook.set_cell_contents('Sheet1', 'B3', "=B2")
    workbook.set_cell_contents('Sheet1', 'A1', '=ISERROR(b2)')
    assert workbook.get_cell_value('Sheet1', 'A1')

    # NOTE: We don't need to handle this case
    workbook.set_cell_contents('Sheet1', 'B2', "=A1")
    workbook.set_cell_contents('Sheet1', 'A1', '=ISERROR(b2)')
    assert workbook.get_cell_value('Sheet1', 'A1')

    workbook.set_cell_contents('Sheet1', 'A1', '=ISERROR(A1)')
    assert is_error(workbook.get_cell_value('Sheet1', 'A1'), CellErrorType.CIRCULAR_REFERENCE)

def test_VERSION_function():
    '''Test VERSION function'''
    workbook = Workbook()
    workbook.new_sheet()

    workbook.set_cell_contents('Sheet1', 'A1', '=VERSION(1)')
    assert is_error(workbook.get_cell_value('Sheet1', 'a1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents('Sheet1', 'A1', '=VERSION()')
    assert workbook.get_cell_value('Sheet1', 'A1') == sheets.version

def test_INDIRECT_function():
    '''Test INDIRECT function'''
    workbook = Workbook()
    workbook.new_sheet("Sheet1")
    workbook.set_cell_contents("Sheet1", "A1", "5")

    workbook.set_cell_contents("Sheet1", "A2", '=INDIRECT(A1)')
    workbook.set_cell_contents("Sheet1", "A3", '=INDIRECT("A1")')
    assert workbook.get_cell_value("Sheet1", "A2") == 5
    assert workbook.get_cell_value("Sheet1", "A3") == 5


    workbook.set_cell_contents("Sheet1", "A2", '=INDIRECT(Sheet1!A1)')
    workbook.set_cell_contents("Sheet1", "A3", '=INDIRECT("Sheet1!A1")')
    assert workbook.get_cell_value("Sheet1", "A2") == 5
    assert workbook.get_cell_value("Sheet1", "A3") == 5

    workbook.set_cell_contents("Sheet1", "A2", '=INDIRECT(nonexistant!A1)')
    workbook.set_cell_contents("Sheet1", "A3", '=INDIRECT("nonexistant!A1")')
    assert is_error(workbook.get_cell_value("Sheet1", "A2"), CellErrorType.BAD_NAME)
    assert is_error(workbook.get_cell_value("Sheet1", "A3"), CellErrorType.BAD_NAME)

    workbook.set_cell_contents("Sheet1", "A2", '=INDIRECT("not a ref")')
    assert is_error(workbook.get_cell_value("Sheet1", "A2"), CellErrorType.TYPE_ERROR)


    workbook.set_cell_contents("Sheet1", "A2", '=INDIRECT("not a ref")')
    workbook.set_cell_contents("Sheet1", "A3", '=INDIRECT(5)')
    assert is_error(workbook.get_cell_value("Sheet1", "A2"), CellErrorType.TYPE_ERROR)
    assert is_error(workbook.get_cell_value("Sheet1", "A3"), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents("Sheet1", "A2", '=INDIRECT(True)')
    workbook.set_cell_contents("Sheet1", "A3", '=INDIRECT("5")')
    assert is_error(workbook.get_cell_value("Sheet1", "A2"), CellErrorType.TYPE_ERROR)
    assert is_error(workbook.get_cell_value("Sheet1", "A3"), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents("Sheet1", "A2", '=INDIRECT(parse error gang)')
    assert is_error(workbook.get_cell_value("Sheet1", "A2"), CellErrorType.PARSE_ERROR)


    workbook.set_cell_contents("Sheet1", "A2", '=INDIRECT(A2)')
    workbook.set_cell_contents("Sheet1", "A3", '=INDIRECT("A3")')
    workbook.set_cell_contents("Sheet1", "A4", '=INDIRECT("A3")')
    assert is_error(workbook.get_cell_value("Sheet1", "A2"), CellErrorType.CIRCULAR_REFERENCE)
    assert is_error(workbook.get_cell_value("Sheet1", "A3"), CellErrorType.CIRCULAR_REFERENCE)
    assert is_error(workbook.get_cell_value("Sheet1", "A4"), CellErrorType.CIRCULAR_REFERENCE)

    workbook.set_cell_contents("Sheet1", "A2", '=INDIRECT(A1)')
    workbook.set_cell_contents("Sheet1", "A1", '="10"')
    assert workbook.get_cell_value("Sheet1", "A2") == "10"

    workbook.set_cell_contents("Sheet1", "A1", '=A2')
    assert is_error(workbook.get_cell_value("Sheet1", "A2"), CellErrorType.CIRCULAR_REFERENCE)

    workbook.set_cell_contents("Sheet1", "A1", '=1/0')
    assert is_error(workbook.get_cell_value("Sheet1", "A2"), CellErrorType.DIVIDE_BY_ZERO)

    workbook.set_cell_contents("Sheet1", "A1", '=INDIRECT(A2)')
    workbook.set_cell_contents("Sheet1", "A2", '=A1')
    assert is_error(workbook.get_cell_value("Sheet1", "A1"), CellErrorType.CIRCULAR_REFERENCE)
    assert is_error(workbook.get_cell_value("Sheet1", "A2"), CellErrorType.CIRCULAR_REFERENCE)
