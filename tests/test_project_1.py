'''Tests for project 1'''
import context

# Now we can import other things
import pytest
from sheets import Workbook, CellError, CellErrorType, cell
from decimal import Decimal

#Helper function to check to CellErrors:
def is_error(val, error_type):
    '''Check if error'''
    if isinstance(val, CellError):
        if val.get_type() == error_type:
            return True
    return False

## PYTEST Tests
def test_add_del_sheets():
    '''test add and delete sheets'''
    workbook = Workbook()
    (_index, _name) = workbook.new_sheet()
    (_index, _name) = workbook.new_sheet("Africa*")
    (_index, _name) = workbook.new_sheet("July totals")
    assert workbook.num_sheets() == 3
    # Delete sheets
    with pytest.raises(KeyError):
        workbook.del_sheet("not a sheet")
    workbook.del_sheet("July Totals")
    assert workbook.num_sheets() == 2
    assert workbook.list_sheets() == ["Sheet1", "Africa*"]
    (_index, _name) = workbook.new_sheet(".?!,:;!@#$%^&*()")
    assert ".?!,:;!@#$%^&*()" in workbook.list_sheets()
    (_index, _name) = workbook.new_sheet("s1")
    (_index, _name) = workbook.new_sheet("s")
    (_index, _name) = workbook.new_sheet("a")

def test_add_unique_sheets():
    '''Add unique sheet names'''
    workbook = Workbook()
    (_index1, _name1) = workbook.new_sheet("Africa*")
    (_index2, name2) = workbook.new_sheet()
    (_index3, _name3) = workbook.new_sheet("July totals")
    assert name2 == "Sheet1"
    with pytest.raises(ValueError):
        (_index, _name) = workbook.new_sheet("Sheet1")
    workbook.del_sheet("Sheet1")
    (_index2, name2) = workbook.new_sheet()
    assert name2 == "Sheet1"

def test_add_bad_sheets():
    '''Test bad sheet names'''
    workbook = Workbook()
    with pytest.raises(ValueError):
        (_index, _name) = workbook.new_sheet("")
    with pytest.raises(ValueError):
        (_index, _name) = workbook.new_sheet(" aaw ")
    with pytest.raises(ValueError):
        (_index, _name) = workbook.new_sheet("a_a")
    with pytest.raises(ValueError):
        (_index, _name) = workbook.new_sheet("a'")
    with pytest.raises(ValueError):
        (_index, _name) = workbook.new_sheet(" abc")
    with pytest.raises(ValueError):
        (_index, _name) = workbook.new_sheet("abc ")
    with pytest.raises(ValueError):
        (_index, _name) = workbook.new_sheet(" abc")


def test_del_add_same_sheet():
    '''Test same name'''
    workbook = Workbook()
    (_index, _name) = workbook.new_sheet("Sheet1")
    (_index, _name) = workbook.new_sheet("Sheet2")
    (_index, _name) = workbook.new_sheet("Sheet3")
    workbook.del_sheet("Sheet2")
    (_index, _name) = workbook.new_sheet("Sheet2")
    assert workbook.list_sheets() == ["Sheet1", "Sheet3", "Sheet2"]

def test_del_sheet_with_dep():
    '''Test deleting sheet with dependencies'''
    workbook = Workbook()
    (_index, _name) = workbook.new_sheet("Sheet1")
    (_index, _name) = workbook.new_sheet("Sheet2")

    workbook.set_cell_contents("Sheet1", "A1", '=Sheet2!A1')
    workbook.del_sheet("sheet2")
    assert is_error(workbook.get_cell_value("Sheet1", "A1"), CellErrorType.BAD_NAME)

def test_del_sheet_with_dep_chain():
    '''Test deleting sheet with depedency chain'''
    workbook = Workbook()
    (_index, _name) = workbook.new_sheet("Sheet1")
    (_index, _name) = workbook.new_sheet("Sheet2")
    (_index, _name) = workbook.new_sheet("Sheet3")

    workbook.set_cell_contents("Sheet1", "A1", '5')
    workbook.set_cell_contents("Sheet2", "A1", '=Sheet1!A1')
    workbook.set_cell_contents("Sheet3", "A1", '=Sheet2!A1')
    workbook.del_sheet("sheet2")

    assert workbook.get_cell_value("Sheet1", "A1") == 5
    assert is_error(workbook.get_cell_value("Sheet3", "A1"), CellErrorType.BAD_NAME)
    with pytest.raises(KeyError):
        workbook.get_cell_value("Sheet2", "A1")

def test_sheet_set_and_extent():
    '''Test set contents and sheet extent'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")
    workbook.set_cell_contents(name, 'B1', '34')
    workbook.set_cell_contents(name, 'A1', '3')
    assert workbook.get_sheet_extent("sheet1")==(2,1)
    (_index, name) = workbook.new_sheet()
    assert workbook.get_sheet_extent("Sheet2")==(0,0)
    with pytest.raises(ValueError):
        workbook.set_cell_contents(name, '0', '5')
    assert workbook.get_sheet_extent("Sheet2")==(0,0)
    workbook.set_cell_contents(name, 'g1', '3')
    assert workbook.get_sheet_extent("Sheet2")==(7,1)
    workbook.set_cell_contents(name, 'A312', '5')
    assert workbook.get_sheet_extent("Sheet2")==(7,312)
    with pytest.raises(ValueError):
        workbook.set_cell_contents(name, 'ZZZZZ312', '5')
    with pytest.raises(ValueError):
        workbook.set_cell_contents(name, '100', '5')
    with pytest.raises(ValueError):
        workbook.set_cell_contents(name, 'A0', '5')
    with pytest.raises(ValueError):
        workbook.set_cell_contents(name, 'A02', '5')
    with pytest.raises(ValueError):
        workbook.set_cell_contents(name, 'A-1', '5')
    with pytest.raises(ValueError):
        workbook.set_cell_contents(name, 'A 1', '5')
    with pytest.raises(ValueError):
        workbook.set_cell_contents(name, ' A1', '5')
    with pytest.raises(ValueError):
        workbook.set_cell_contents(name, 'A1 ', '5')
    with pytest.raises(ValueError):
        workbook.set_cell_contents(name, '', '5')
    workbook.set_cell_contents(name, 'A9999', '5')
    assert workbook.get_sheet_extent("Sheet2")==(7,9999)
    with pytest.raises(ValueError):
        workbook.set_cell_contents(name, 'A10000', '5')
    workbook.set_cell_contents(name, 'ZZZZ9999', '5')
    assert workbook.get_sheet_extent("Sheet2")==(475254,9999)
    workbook.set_cell_contents(name, 'ZZ99', '5')
    assert workbook.get_sheet_extent("Sheet2")==(475254,9999)

def test_extent_decrease():
    '''Test change in extent'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")
    workbook.set_cell_contents(name, 'B2', '5')
    assert workbook.get_sheet_extent("sheet1")==(2,2)
    workbook.set_cell_contents(name, 'B2', '')
    assert workbook.get_sheet_extent("sheet1")==(0,0)
    workbook.set_cell_contents(name, 'B2', '5')
    assert workbook.get_sheet_extent("sheet1")==(2,2)
    workbook.set_cell_contents(name, 'B2', None)
    assert workbook.get_sheet_extent("sheet1")==(0,0)

def test_different_workbooks_sheets():
    '''Test multiple sheets'''
    workbook = Workbook()
    (_index1, name1) = workbook.new_sheet("sheet1")
    (_index2, name2) = workbook.new_sheet("sheet2")
    workbook2 = Workbook()
    (_index3, name3) = workbook2.new_sheet("sheet3")
    workbook.set_cell_contents(name1, 'B2', "boof")
    assert workbook.get_cell_value(name1, "b2") == "boof"
    workbook.set_cell_contents(name2, 'C2', 'boof2')
    assert workbook.get_cell_value(name2, "C2") == "boof2"
    workbook2.set_cell_contents(name3, 'f3', 'boof3')
    assert workbook2.get_cell_value(name3, "f3") == "boof3"

def test_parse_cell_contents():
    '''Test parsing contents'''
    assert cell.parse_cell_contents("1") == Decimal("1")
    assert cell.parse_cell_contents(" 1") == Decimal("1")
    assert cell.parse_cell_contents("1 ") == Decimal("1")
    assert cell.parse_cell_contents("-0.5") == Decimal("-.5")
    assert cell.parse_cell_contents("=A1 + 1") == "=A1 + 1"
    assert cell.parse_cell_contents(" =A1 +   1  ") == "=A1 +   1"
    assert cell.parse_cell_contents("'baloon") == "baloon"
    assert cell.parse_cell_contents("asd") == "asd"
    assert cell.parse_cell_contents("") is None
    assert cell.parse_cell_contents(None) is None
    assert cell.parse_cell_contents("      ") is None
    assert cell.parse_cell_contents("NaN") == "NaN"
    assert cell.parse_cell_contents("Infinity") == "Infinity"
    assert cell.parse_cell_contents("'Infinity") == "Infinity"
    assert cell.parse_cell_contents("'") == ""

def test_random_formulas():
    '''Test different formulas'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet()
    workbook.set_cell_contents(name, 'B2', '=5')
    assert workbook.get_cell_value(name, "b2") == Decimal("5")
    workbook.set_cell_contents(name, 'B2', '=A1')
    assert workbook.get_cell_value(name, "b2") == Decimal("0")
    workbook.set_cell_contents(name, 'a1', '=5')
    assert workbook.get_cell_value(name, "b2") == Decimal("5")
    workbook.set_cell_contents(name, 'g23', "'=boof")
    assert workbook.get_cell_value(name, "g23") == "=boof"

def test_literals():
    '''Test typing'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet()
    workbook.set_cell_contents(name, 'B2', 'lol')
    assert workbook.get_cell_value(name, "b2") == "lol"
    workbook.set_cell_contents(name, 'g3', "'stinky")
    assert workbook.get_cell_value(name, "g3") == "stinky"
    workbook.set_cell_contents(name, 'l53', "NaN")
    assert workbook.get_cell_value(name, "l53") == "NaN"
    workbook.set_cell_contents(name, 'r6', '=l53  &   "5"')
    assert workbook.get_cell_value(name, "r6") == "NaN5"
    workbook.set_cell_contents(name, 'g6', '=l53  +  5')
    assert is_error(workbook.get_cell_value(name, "g6"),CellErrorType.TYPE_ERROR)
    workbook.set_cell_contents(name, 'g6', '=3 * "abc"')
    assert is_error(workbook.get_cell_value(name, "g6"),CellErrorType.TYPE_ERROR)

def test_unary():
    '''Test unary functions'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet()
    workbook.set_cell_contents(name, 'B2', "5")
    workbook.set_cell_contents(name, 'B3', "-5")
    assert workbook.get_cell_value(name, "b3") == -5
    workbook.set_cell_contents(name, 'B4', "=-B2")
    assert workbook.get_cell_value(name, "b4") == -5
    workbook.set_cell_contents(name, 'B5', "=+B2")
    assert workbook.get_cell_value(name, "b5") == 5
    workbook.set_cell_contents(name, 'B6', '=7*-"10"')
    assert workbook.get_cell_value(name, "b6") == -70
    workbook.set_cell_contents(name, 'B7', '=-(+5)')
    assert workbook.get_cell_value(name, "b7") == -5
    workbook.set_cell_contents(name, 'B8', '=+(-5)')
    assert workbook.get_cell_value(name, "b8") == -5

def test_decimals_large():
    '''Test decimal conversion'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet()
    workbook.set_cell_contents(name, 'B2', "0.0000023")
    workbook.set_cell_contents(name, 'B3', "-545")
    assert workbook.get_cell_value(name, "b2") == Decimal("0.0000023")
    assert workbook.get_cell_value(name, "b3") == Decimal("-545")
    workbook.set_cell_contents(name, 'B4', "=b2 * b3")
    assert workbook.get_cell_value(name, "b4") == Decimal("-0.0012535")
    workbook.set_cell_contents(name, 'B5', "=b4 - 100.2")
    assert workbook.get_cell_value(name, "b5") == Decimal("-100.2012535")
    workbook.set_cell_contents(name, 'B6', "=b5 / 100.2012535")
    assert workbook.get_cell_value(name, "b6") == Decimal("-1")

def test_reference_other_sheet():
    '''Test references to other sheets'''
    workbook = Workbook()
    (_index1, name1) = workbook.new_sheet()
    (_index2, name2) = workbook.new_sheet("()()($%@$!%!")
    (_index3, name3) = workbook.new_sheet()
    workbook.set_cell_contents(name1, 'B2', "5")
    workbook.set_cell_contents(name1, 'B3', "=b2+7")
    workbook.set_cell_contents(name2, 'B2', "=Sheet1!B3 * 5")
    workbook.set_cell_contents(name2, 'B4', "=sheet1!b3 * 5")
    workbook.set_cell_contents(name2, 'B3', "=b2-50")
    workbook.set_cell_contents(name3, 'B3', "='()()($%@$!%!'!b3 + 5")
    workbook.set_cell_contents(name3, 'B4', "=()()($%@$!%!!b3 + 5")
    workbook.set_cell_contents(name3, 'B5', "=sheet100!b3 + 5")
    assert workbook.get_cell_value(name1, "b2") == 5
    assert workbook.get_cell_value(name1, "b3") == 12
    assert workbook.get_cell_value(name2, "b2") == 60
    assert workbook.get_cell_value(name2, "b2") == workbook.get_cell_value(name2, "b4")
    assert workbook.get_cell_value(name2, "b3") == 10
    assert workbook.get_cell_value(name3, "b3") == 15
    assert is_error(workbook.get_cell_value(name3, "b4"),CellErrorType.PARSE_ERROR)
    assert is_error(workbook.get_cell_value(name3, "b5"),CellErrorType.BAD_NAME)
    (_index4, name4) = workbook.new_sheet("SHEET100")
    # failure here bc not updating
    workbook.set_cell_contents(name4, 'B3', "7")
    assert workbook.get_cell_value(name3, "b5") == 12

def test_reference_same_sheet():
    '''Test normal references'''
    workbook = Workbook()
    (_index1, name1) = workbook.new_sheet()
    workbook.set_cell_contents(name1, 'B2', "=A1")
    assert workbook.get_cell_value(name1, "b2") == 0
    workbook.set_cell_contents(name1, 'a1', "5")
    assert workbook.get_cell_value(name1, "b2") == 5

def test_concat_numbers():
    '''Test string concat'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet()
    workbook.set_cell_contents(name, 'B1', '=5 & "lol"')
    assert workbook.get_cell_value(name, "b1") == "5lol"
    workbook.set_cell_contents(name, 'B2', "5")
    assert workbook.get_cell_value(name, "b2") == 5
    workbook.set_cell_contents(name, 'a1', '=b2 & "hello" & (3 + 4 * 2)')
    assert workbook.get_cell_value(name, "a1") == "5hello11"
    workbook.set_cell_contents(name, 'B3', '=B2 & "BOOF"')
    assert workbook.get_cell_value(name, "b3") == "5BOOF"
    workbook.set_cell_contents(name, 'B4', "=b2 * 10")
    assert workbook.get_cell_value(name, "b4") == 50
    workbook.set_cell_contents(name, 'B5', '=B4 & "BOOF"')
    assert workbook.get_cell_value(name, "b5") == "50BOOF"
    workbook.set_cell_contents(name, 'B4', "=b2 * 0.01")
    assert workbook.get_cell_value(name, "b5") == "0.05BOOF"
    workbook.set_cell_contents(name, 'B6', '')
    assert workbook.get_cell_value(name, "b6") is None
    workbook.set_cell_contents(name, 'B7', '=B6 & "BOOF"')
    assert workbook.get_cell_value(name, "b7") == "BOOF"
    workbook.set_cell_contents(name, 'B8', "'boof")
    assert workbook.get_cell_value(name, "b8") == "boof"
    workbook.set_cell_contents(name, 'B9', '=B8 & (27 + 3)')
    assert workbook.get_cell_value(name, "b9") == "boof30"
    workbook.set_cell_contents(name, 'B10', '=4.3 * ("hello" & B5)')
    assert is_error(workbook.get_cell_value(name, "b10"),CellErrorType.TYPE_ERROR)

def test_random_errors():
    '''Test different errors'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet()
    workbook.set_cell_contents(name, 'a1', "=inf + 3")
    assert is_error(workbook.get_cell_value(name, "a1"),CellErrorType.PARSE_ERROR)
    workbook.set_cell_contents(name, 'b1', '="inf" + 3')
    assert is_error(workbook.get_cell_value(name, "b1"),CellErrorType.TYPE_ERROR)
    workbook.set_cell_contents(name, 'c1', '="inf" & "hello"')
    assert workbook.get_cell_value(name, "c1") == "infhello"

def test_single_quotes():
    '''Test strings with single quotes'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet()
    workbook.set_cell_contents(name, 'a1', "'")
    assert workbook.get_cell_value(name, "a1") == ""
    workbook.set_cell_contents(name, 'b1', "")
    assert workbook.get_cell_value(name, "b1") is None
    assert workbook.get_sheet_extent("sheet1")==(1,1)

def test_operations_on_strings():
    '''Test string conversions'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet()
    workbook.set_cell_contents(name, 'B2', "'5")
    assert workbook.get_cell_value(name, "b2") == Decimal(5)
    workbook.set_cell_contents(name, 'B3', "=20 * b2")
    assert workbook.get_cell_value(name, "b3") == 100
    workbook.set_cell_contents(name, 'B4', "=b2 / 5")
    assert workbook.get_cell_value(name, "b4") == 1
    workbook.set_cell_contents(name, 'B5', "=b2 + 5")
    assert workbook.get_cell_value(name, "b5") == 10
    workbook.set_cell_contents(name, 'B6', "=b2 - 5")
    assert workbook.get_cell_value(name, "b6") == 0
    workbook.set_cell_contents(name, 'B7', "=-b2")
    assert workbook.get_cell_value(name, "b7") == -5
    workbook.set_cell_contents(name, 'B8', "=+b2")
    assert workbook.get_cell_value(name, "b8") == 5
    workbook.set_cell_contents(name, 'B9', "=-(b2)")
    assert workbook.get_cell_value(name, "b9") == -5
    workbook.set_cell_contents(name, 'c1', "=+(-b2)")
    assert workbook.get_cell_value(name, "c1") == -5

def test_random_white_space():
    '''Test parser on whitespaces'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet()
    workbook.set_cell_contents(name, 'a1', " '5")
    assert workbook.get_cell_value(name, "a1") == Decimal(5)
    workbook.set_cell_contents(name, 'a2', "    =   a1 + 7   ")
    assert workbook.get_cell_contents(name, "a2") == "=   a1 + 7"
    assert workbook.get_cell_value(name, "a2") == 12

def test_unique_strings():
    '''Test interesting strings'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet()
    workbook.set_cell_contents(name, 'a1', "string_value")
    assert workbook.get_cell_value(name, "a1") == "string_value"
    workbook.set_cell_contents(name, 'a2', "\"string_value\"")
    assert workbook.get_cell_value(name, "a2") == '"string_value"'
    workbook.set_cell_contents(name, 'a3', "=A1&A2")
    assert workbook.get_cell_value(name, "a3") == 'string_value"string_value"'
    workbook.set_cell_contents(name, 'a4', '=A1&\"s\"')
    assert workbook.get_cell_value(name, "a4") == "string_values"
    workbook.set_cell_contents(name, 'a5', "=A2&'other'")
    assert is_error(workbook.get_cell_value(name, "a5"),CellErrorType.PARSE_ERROR)

def test_set_cell_contents_whitespace():
    '''Test whitespace removal'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")

    # remove whitespace
    workbook.set_cell_contents(name, 'F3', '   5')
    assert workbook.get_cell_value(name, 'F3') == 5
    workbook.set_cell_contents(name, 'F4', '5    ')
    assert workbook.get_cell_value(name, 'F4') == 5
    workbook.set_cell_contents(name, 'F5', '   5    ')
    assert workbook.get_cell_value(name, 'F5') == 5

def test_set_bad_cell():
    '''Test cell errors'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")
    workbook.set_cell_contents(name, 'B1', '34')
    workbook.set_cell_contents(name, 'A1', '3')
    workbook.set_cell_contents(name, 'ZZZZ9999', 'hello')
    with pytest.raises(ValueError):
        workbook.set_cell_contents(name, 'ZZZZZ312', '5')
    with pytest.raises(ValueError):
        workbook.set_cell_contents(name, '100', '5')
    with pytest.raises(ValueError):
        workbook.set_cell_contents(name, 'A0', '5')
    with pytest.raises(ValueError):
        workbook.set_cell_contents(name, 'A02', '5')
    with pytest.raises(ValueError):
        workbook.set_cell_contents(name, 'A-1', '5')
    with pytest.raises(ValueError):
        workbook.set_cell_contents(name, '', '5')
    workbook.set_cell_contents(name, 'A9999', '5')
    #####NOTE: Is a bad cel supposed to trigger a ValueError?

def test_cell_ref():
    '''Test cell references'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet()
    (_index2, name2) = workbook.new_sheet()

    workbook.set_cell_contents(name, "a1", "1")
    workbook.set_cell_contents(name, "a2", "= a1")
    assert workbook.get_cell_value(name, "a2") == 1

    workbook.set_cell_contents(name2, "a2", "= {}!a1".format(name))
    assert workbook.get_cell_value(name2, "a2") == 1
    workbook.set_cell_contents(name2, "a2", "= '{}'!a1".format(name))
    assert workbook.get_cell_value(name2, "a2") == 1

    # Reference non-set cell
    workbook.set_cell_contents(name, 'e1', '= A5')
    assert workbook.get_cell_value(name, 'e1') == 0

    # Reference non-set cell
    workbook.set_cell_contents(name, 'r1', '= A5 + A5/3')
    assert workbook.get_cell_value(name, 'r1') == 0

    # Bad name errors in cell references
    workbook.set_cell_contents(name2, "a2", "= nonexistent!a1")
    assert is_error(workbook.get_cell_value(name2, 'a2'), CellErrorType.BAD_NAME)

    workbook.set_cell_contents(name2, "a2", "= {}!zzzzz1".format(name))
    assert is_error(workbook.get_cell_value(name2, 'a2'), CellErrorType.BAD_NAME)


def test_cell_concatenation():
    '''Test string concatenation'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")
    workbook.set_cell_contents(name, 'c1', 'hello')
    workbook.set_cell_contents(name, 'd1', '= c1 & C1')
    assert workbook.get_cell_value(name, "d1") == "hellohello"

    # Concat numbers
    workbook.set_cell_contents(name, 'c1', '5')
    workbook.set_cell_contents(name, 'd1', '= c1 & C1')
    assert workbook.get_cell_value(name, "d1") == "55"

    workbook.set_cell_contents(name, 'e1', '= d1 & "hello"')
    assert workbook.get_cell_value(name, "e1") == "55hello"

    workbook.set_cell_contents(name, 'c1', "'Infinity")
    workbook.set_cell_contents(name, 'd1', '= c1 & "Nan"')
    assert workbook.get_cell_value(name, "d1") == "InfinityNan"



def test_cell_addition():
    '''Test addition'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")
    workbook.set_cell_contents(name, 'b1', '1')
    workbook.set_cell_contents(name, 'c1', '= 1 - b1')
    workbook.set_cell_contents(name, 'd1', '="-3.0" - 1')
    workbook.set_cell_contents(name, 'e1', '=-3.0 - b1')

    assert workbook.get_cell_value(name, 'd1') == Decimal(-4)
    assert workbook.get_cell_value(name, 'e1') == Decimal(-4)

    workbook.set_cell_contents(name, "c1", "'5")
    workbook.set_cell_contents(name, 'd1', '= 1 - c1')
    assert workbook.get_cell_value(name, 'd1') == Decimal(-4)

    workbook.set_cell_contents(name, 'd1', '= c1 - c1 - 4')
    assert workbook.get_cell_value(name, 'd1') == Decimal(-4)

    workbook.set_cell_contents(name, "c1", "hello")
    workbook.set_cell_contents(name, 'd1', '= 1 - c1')
    assert is_error(workbook.get_cell_value(name, 'd1'), CellErrorType.TYPE_ERROR)

def test_cell_multiplication():
    '''Test multiplication'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")
    workbook.set_cell_contents(name, 'b1', '1')
    workbook.set_cell_contents(name, 'c1', '= 2 * b1')
    workbook.set_cell_contents(name, 'd1', '= -3.0/b1')
    assert workbook.get_cell_value(name, 'c1') == Decimal(2)
    assert workbook.get_cell_value(name, 'd1') == Decimal(-3)

    workbook.set_cell_contents(name, "c1", "hello")
    workbook.set_cell_contents(name, 'd1', '= 1 * c1')
    assert is_error(workbook.get_cell_value(name, 'd1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents(name, 'd1', '= 1 / 0')
    assert is_error(workbook.get_cell_value(name, 'd1'), CellErrorType.DIVIDE_BY_ZERO)

def test_inf_nan_operations():
    '''Test Inf and NaN operations'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")

    #Multiplication + Division for all inf/nan strings
    workbook.set_cell_contents(name, "c1", "Inf")
    workbook.set_cell_contents(name, 'd1', '= 1 * c1')
    assert is_error(workbook.get_cell_value(name, 'd1'), CellErrorType.TYPE_ERROR)
    workbook.set_cell_contents(name, "c1", "Nan")
    workbook.set_cell_contents(name, 'd1', '= 1 * c1')
    assert is_error(workbook.get_cell_value(name, 'd1'), CellErrorType.TYPE_ERROR)
    workbook.set_cell_contents(name, "c1", "-Infinity")
    workbook.set_cell_contents(name, 'd1', '= 1 * c1')
    assert is_error(workbook.get_cell_value(name, 'd1'), CellErrorType.TYPE_ERROR)
    workbook.set_cell_contents(name, "c1", "-Nan")
    workbook.set_cell_contents(name, 'd1', '= 1 * c1')
    assert is_error(workbook.get_cell_value(name, 'd1'), CellErrorType.TYPE_ERROR)
    workbook.set_cell_contents(name, "c1", "-nan")
    workbook.set_cell_contents(name, 'd1', '= 1 + c1')
    assert is_error(workbook.get_cell_value(name, 'd1'), CellErrorType.TYPE_ERROR)

    # Test addition/subtractions
    workbook.set_cell_contents(name, 'd1', '= 1 - c1')
    assert is_error(workbook.get_cell_value(name, 'd1'), CellErrorType.TYPE_ERROR)
    workbook.set_cell_contents(name, 'd1', '= 1 + c1')
    assert is_error(workbook.get_cell_value(name, 'd1'), CellErrorType.TYPE_ERROR)

    # Unary Operations
    workbook.set_cell_contents(name, 'd1', '= -c1')
    assert is_error(workbook.get_cell_value(name, 'd1'), CellErrorType.TYPE_ERROR)
    workbook.set_cell_contents(name, 'd1', '= +c1')
    assert is_error(workbook.get_cell_value(name, 'd1'), CellErrorType.TYPE_ERROR)

def test_cell_combined_ops():
    '''Test multiple operations'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")
    #Multiplication + Division operations
    workbook.set_cell_contents(name, "a1", "'1")
    workbook.set_cell_contents(name, "b1", '=a1 & "hello" & (3 + 4 * 2)')
    assert workbook.get_cell_value(name, "b1") == "1hello11"

    workbook.set_cell_contents(name, "b1", '=4.3 * ("hello" & a5)')
    assert is_error(workbook.get_cell_value(name, 'b1'), CellErrorType.TYPE_ERROR)

def test_cell_updating():
    '''Test updating cells'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")
    workbook.set_cell_contents(name, 'a1', '1')
    workbook.set_cell_contents(name, 'a2', '= 1 + a1')
    workbook.set_cell_contents(name, 'a3', '= 1 + a2')
    workbook.set_cell_contents(name, 'a4', '= a1 + a3')


    workbook.set_cell_contents(name, 'a1', None)
    assert workbook.get_cell_value(name, "a2") == 1
    assert workbook.get_cell_value(name, "a3") == 2
    assert workbook.get_cell_value(name, "a4") == 2

def test_cell_updating_error_prop():
    '''Test error propogation'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")
    workbook.set_cell_contents(name, 'a1', '1')
    workbook.set_cell_contents(name, 'a2', '= 1 + a1')
    workbook.set_cell_contents(name, 'a3', '= 1 + a2')
    workbook.set_cell_contents(name, 'a4', '= a1 + a3')

    workbook.set_cell_contents(name, 'a1', "string")
    assert is_error(workbook.get_cell_value(name, 'a2'), CellErrorType.TYPE_ERROR)
    assert is_error(workbook.get_cell_value(name, 'a3'), CellErrorType.TYPE_ERROR)
    assert is_error(workbook.get_cell_value(name, 'a4'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents(name, 'a1', "1")
    assert workbook.get_cell_value(name, 'a2') == 2
    assert workbook.get_cell_value(name, 'a3') == 3
    assert workbook.get_cell_value(name, 'a4') == 4


def test_circular_ref():
    '''Test circular reference error'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")

    # Simple circular reference
    workbook.set_cell_contents(name, 'a1', '= b1')
    workbook.set_cell_contents(name, "b1", "= a1")
    workbook.set_cell_contents(name, "c1", "=a1 * 5")
    assert is_error(workbook.get_cell_value(name, 'a1'), CellErrorType.CIRCULAR_REFERENCE)
    assert is_error(workbook.get_cell_value(name, 'b1'), CellErrorType.CIRCULAR_REFERENCE)
    assert is_error(workbook.get_cell_value(name, 'c1'), CellErrorType.CIRCULAR_REFERENCE)


    # Now undo the circular refernce:
    workbook.set_cell_contents(name, 'a1', '1')
    assert workbook.get_cell_value(name, "a1") == 1
    assert workbook.get_cell_value(name, "b1") == 1
    assert workbook.get_cell_value(name, "c1") == 5


def test_circular_ref_parent_cell():
    ''' Circular reference that depends on a cell'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")

    workbook.set_cell_contents(name, 'c1', '1')
    workbook.set_cell_contents(name, 'a1', '= b1 + c1')
    workbook.set_cell_contents(name, "b1", "= a1")
    assert workbook.get_cell_value(name, "c1") == 1
    assert is_error(workbook.get_cell_value(name, 'a1'), CellErrorType.CIRCULAR_REFERENCE)
    assert is_error(workbook.get_cell_value(name, 'b1'), CellErrorType.CIRCULAR_REFERENCE)

    workbook.set_cell_contents(name, 'l1', '1')
    workbook.set_cell_contents(name, 'c1', '= l1')
    assert workbook.get_cell_value(name, "c1") == 1
    assert workbook.get_cell_value(name, "l1") == 1
    assert is_error(workbook.get_cell_value(name, 'a1'), CellErrorType.CIRCULAR_REFERENCE)
    assert is_error(workbook.get_cell_value(name, 'b1'), CellErrorType.CIRCULAR_REFERENCE)

def test_sheet_delete_add_dep():
    '''Test sheet changes with dependencies'''
    workbook = Workbook()
    (_index0, name0) = workbook.new_sheet()
    (_index1, name1) = workbook.new_sheet()


    workbook.set_cell_contents(name0, 'a1', '=non!a1')
    assert is_error(workbook.get_cell_value(name0, 'a1'), CellErrorType.BAD_NAME)
    workbook.del_sheet(name0)
    with pytest.raises(KeyError):
        workbook.get_cell_value(name0, "a1")



    workbook.set_cell_contents(name1, 'a1', '=non!a1')
    workbook.set_cell_contents(name1, 'a2', '=non!a1')
    workbook.set_cell_contents(name1, 'a3', '=a1')
    assert is_error(workbook.get_cell_value(name1, 'a1'), CellErrorType.BAD_NAME)
    assert is_error(workbook.get_cell_value(name1, 'a2'), CellErrorType.BAD_NAME)
    assert is_error(workbook.get_cell_value(name1, 'a3'), CellErrorType.BAD_NAME)


    (_index2, _name2) = workbook.new_sheet("non")
    assert workbook.get_cell_value(name1, "a1") == 0
    assert workbook.get_cell_value(name1, "a2") == 0
    assert workbook.get_cell_value(name1, "a3") == 0


    workbook.set_cell_contents("non", "a1", "5")
    assert workbook.get_cell_value(name1, "a1") == 5
    assert workbook.get_cell_value(name1, "a2") == 5
    assert workbook.get_cell_value(name1, "a3") == 5


    workbook.del_sheet("non")
    assert is_error(workbook.get_cell_value(name1, 'a1'), CellErrorType.BAD_NAME)
    assert is_error(workbook.get_cell_value(name1, 'a2'), CellErrorType.BAD_NAME)
    assert is_error(workbook.get_cell_value(name1, 'a3'), CellErrorType.BAD_NAME)

def test_error_prop():
    '''Test more error prop'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")

    workbook.set_cell_contents(name, 'c1', '20')
    workbook.set_cell_contents(name, 'a1', '=  c1 / 0  ')
    workbook.set_cell_contents(name, "b1", "= a1 + 5")
    assert workbook.get_cell_value(name, "c1") == 20
    assert is_error(workbook.get_cell_value(name, 'a1'), CellErrorType.DIVIDE_BY_ZERO)
    assert is_error(workbook.get_cell_value(name, 'b1'), CellErrorType.DIVIDE_BY_ZERO)

    workbook.set_cell_contents(name, 'a1', '=  c1 / 2  ')
    workbook.set_cell_contents(name, "b1", "= a1 + 5")
    assert workbook.get_cell_value(name, "a1") == 10
    assert workbook.get_cell_value(name, "b1") == 15

    workbook.set_cell_contents(name, 'c1', '20')
    workbook.set_cell_contents(name, 'a1', '=  c1 + "boof"')
    workbook.set_cell_contents(name, "b1", "= a1 + 5")
    assert workbook.get_cell_value(name, "c1") == 20
    assert is_error(workbook.get_cell_value(name, 'a1'), CellErrorType.TYPE_ERROR)
    assert is_error(workbook.get_cell_value(name, 'b1'), CellErrorType.TYPE_ERROR)

    workbook.set_cell_contents(name, 'a1', '=  c1 + "2"  ')
    workbook.set_cell_contents(name, "b1", "= a1 + 5")
    assert workbook.get_cell_value(name, "a1") == 22
    assert workbook.get_cell_value(name, "b1") == 27

    workbook.set_cell_contents(name, 'a1', '=  zzzzzzz1')
    assert is_error(workbook.get_cell_value(name, 'a1'), CellErrorType.BAD_NAME)

def test_complicated_situation():
    '''Test unique situations'''
    workbook = Workbook()
    (_index, name) = workbook.new_sheet("sheet1")

    workbook.set_cell_contents(name, 'a1', '5')
    workbook.set_cell_contents(name, 'b1', '=  a1 +c1')
    assert workbook.get_cell_value(name, "b1") == 5
    workbook.set_cell_contents(name, "c1", "= d1 + a1")
    assert workbook.get_cell_value(name, "c1") == 5
    workbook.set_cell_contents(name, "d1", "= a1 + b1")
    assert workbook.get_cell_value(name, "a1") == 5
    assert is_error(workbook.get_cell_value(name, 'b1'), CellErrorType.CIRCULAR_REFERENCE)
    assert is_error(workbook.get_cell_value(name, 'c1'), CellErrorType.CIRCULAR_REFERENCE)
    assert is_error(workbook.get_cell_value(name, 'b1'), CellErrorType.CIRCULAR_REFERENCE)
    workbook.set_cell_contents(name, "c1", "= 10 + a1")
    assert workbook.get_cell_value(name, "c1") == 15
    assert workbook.get_cell_value(name, "b1") == 20
    assert workbook.get_cell_value(name, "d1") == 25

    (_index2, name2) = workbook.new_sheet("sheet2")
    workbook.set_cell_contents(name2, 'a1', '=b2/0')
    assert is_error(workbook.get_cell_value(name2, 'a1'), CellErrorType.DIVIDE_BY_ZERO)
    workbook.set_cell_contents(name, 'a1', '=\'sheet2\'!a1 + 5')
    assert is_error(workbook.get_cell_value(name, 'a1'), CellErrorType.DIVIDE_BY_ZERO)
    workbook.set_cell_contents(name2, 'a1', '=b2/5')
    assert workbook.get_cell_value(name2, "b2") is None
    assert workbook.get_cell_value(name, "a1") == 5
    assert workbook.get_cell_value(name2, "a1") == 0
