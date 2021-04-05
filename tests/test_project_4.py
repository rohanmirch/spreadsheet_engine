'''Tests for project 4'''
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

def test_ranges_as_contents():
    '''Test setting range as contents'''
    book = Workbook()

    book.new_sheet("S")
    book.set_cell_contents("S", "A1", "=B1:B100")
    # type error?
    assert is_error(book.get_cell_value('S', 'a1'), CellErrorType.PARSE_ERROR)

def test_single_cell_range():
    '''Test a range of only one cell'''
    book = Workbook()

    book.new_sheet("S")
    book.set_cell_contents("S", "A1", "5")
    book.set_cell_contents("S", "B1", "=SUM(A1:a1)")
    assert book.get_cell_value('S', 'b1') == 5

def test_single_cell_range_more():
    '''Test errors of ranges being returned'''
    book = Workbook()

    book.new_sheet("S")
    book.set_cell_contents("S", "B1", '=INDIRECT("A1:a1")')
    assert is_error(book.get_cell_value('S', 'b1'), CellErrorType.TYPE_ERROR)

    book.set_cell_contents("S", "A1", '=CHOOSE(1, C1:D1)')
    assert is_error(book.get_cell_value('S', 'A1'), CellErrorType.TYPE_ERROR)

    assert is_error(book.get_cell_value('S', 'b1'), CellErrorType.TYPE_ERROR)

def test_MIN():
    '''Test MIN basics'''
    book = Workbook()

    book.new_sheet("S")
    book.set_cell_contents("S", "A1", "1")

    book.set_cell_contents("S", "B1", "= MIN(A1)")
    assert book.get_cell_value("S", "B1") == 1

    # ALl refs empty cells
    book.set_cell_contents("S", "B1", "= MIN(Z1)")
    assert book.get_cell_value("S", "B1") == 0

    book.set_cell_contents("S", "B1", "= MIN(Z3:Z1)")
    assert book.get_cell_value("S", "B1") == 0

    book.set_cell_contents("S", "B1", "= MIN(A1, Z1)")
    assert book.get_cell_value("S", "B1") is None

    book.set_cell_contents("S", "A2", "2")
    book.set_cell_contents("S", "B1", "= MIN(A1:A2)")
    assert book.get_cell_value("S", "B1") == 1

    book.set_cell_contents("S", "A2", "2")
    book.set_cell_contents("S", "A3", "0")

    book.set_cell_contents("S", "B1", "= MIN(A1:A2, Z1)")
    assert book.get_cell_value("S", "B1") is None
    book.set_cell_contents("S", "B1", "= MIN(A1:A2, A3)")
    assert book.get_cell_value("S", "B1") == 0

def test_MIN_more():
    '''Test more complicated MIN'''
    book = Workbook()
    book.new_sheet("S")

    book.set_cell_contents("S", "A1", "= MIN(0, False)")
    assert book.get_cell_value("S", "A1") == 0

    book.set_cell_contents("S", "A1", "= MIN(FALSE, 0, -1, True)")
    assert book.get_cell_value("S", "A1") == -1

def test_MIN_errors():
    '''Test errors with MIN'''
    book = Workbook()

    book.new_sheet("S")
    book.set_cell_contents("S", "A1", "1")


    book.set_cell_contents("S", "B1", "= MIN()")
    assert is_error(book.get_cell_value("S", "B1"), CellErrorType.TYPE_ERROR)

    book.set_cell_contents("S", "B1", "= MIN(A1:A99999)")
    assert is_error(book.get_cell_value("S", "B1"), CellErrorType.BAD_NAME)

    book.set_cell_contents("S", "B1", "= MIN(B1)")
    assert is_error(book.get_cell_value("S", "B1"), CellErrorType.CIRCULAR_REFERENCE)

def test_MAX():
    '''Test MAX basics'''
    book = Workbook()
    book.new_sheet("S")
    book.set_cell_contents("S", "A1", "1")

    book.set_cell_contents("S", "B1", "= MAX(A1)")
    assert book.get_cell_value("S", "B1") == 1

    # ALl refs empty cells
    book.set_cell_contents("S", "B1", "= MAX(Z1)")
    assert book.get_cell_value("S", "B1") == 0

    book.set_cell_contents("S", "B1", "= MAX($Z3:Z1)")
    assert book.get_cell_value("S", "B1") == 0

    book.set_cell_contents("S", "B1", "= MAX(A1, Z1)")
    assert book.get_cell_value("S", "B1") == 1

    book.set_cell_contents("S", "A2", "2")
    book.set_cell_contents("S", "B1", "= MAX(A1:$A$2)")
    assert book.get_cell_value("S", "B1") == 2


def test_MAX_more():
    '''Test more complicated MAX'''
    book = Workbook()
    book.new_sheet("S")

    book.set_cell_contents("S", "A1", "= MAX(0, False)")
    assert not book.get_cell_value("S", "A1")

    book.set_cell_contents("S", "A1", "= MAX(FALSE, 0, -1, True)")
    assert book.get_cell_value("S", "A1")

    book.set_cell_contents("S", "A1", '= MAX("lol", 5)')
    assert book.get_cell_value("S", "A1") == "lol"

def test_MAX_errors():
    '''Test MAX errors'''
    book = Workbook()

    book.new_sheet("S")
    book.set_cell_contents("S", "A1", "1")


    book.set_cell_contents("S", "B1", "= MAX()")
    assert is_error(book.get_cell_value("S", "B1"), CellErrorType.TYPE_ERROR)

    book.set_cell_contents("S", "B1", "= MAX(A1:A99999, 5)")
    assert is_error(book.get_cell_value("S", "B1"), CellErrorType.BAD_NAME)

    book.set_cell_contents("S", "B1", "= MAX(B1)")
    assert is_error(book.get_cell_value("S", "B1"), CellErrorType.CIRCULAR_REFERENCE)

    book.set_cell_contents("S", "B1", "= MAX(1/0)")
    assert is_error(book.get_cell_value("S", "B1"), CellErrorType.TYPE_ERROR)

    book.set_cell_contents("S", "B2", "= MAX(B1)")
    assert is_error(book.get_cell_value("S", "B2"), CellErrorType.TYPE_ERROR)

def test_SUM():
    '''Test SUM basics'''
    book = Workbook()
    book.new_sheet("Sheet1")


    book.set_cell_contents("Sheet1", "A1", '=SUM(1,2,3)')
    assert book.get_cell_value("Sheet1", "A1") == 6

    book.set_cell_contents("Sheet1", "A1", '=SUM(1, A2:A4)')
    assert book.get_cell_value("Sheet1", "A1") == 1

    book.set_cell_contents("Sheet1", "A1", '=SUM(1, TRUE)')
    assert book.get_cell_value("Sheet1", "A1") == 2

    book.set_cell_contents("Sheet1", "A1", '=SUM(1, "5")')
    assert book.get_cell_value("Sheet1", "A1") == 6

    book.set_cell_contents("Sheet1", "A1", '=SUM(A2:A4)')
    assert book.get_cell_value("Sheet1", "A1") == 0

def test_SUM_errors():
    '''Test errors from SUM'''
    book = Workbook()
    book.new_sheet("Sheet1")



    book.set_cell_contents("Sheet1", "A1", '=SUM()')
    assert is_error(book.get_cell_value("Sheet1", "A1"), CellErrorType.TYPE_ERROR)

    book.set_cell_contents("Sheet1", "A1", '=SUM(1, "hello")')
    assert is_error(book.get_cell_value("Sheet1", "A1"), CellErrorType.TYPE_ERROR)

    book.set_cell_contents("Sheet1", "A1", '=SUM(1, 1/0)')
    assert is_error(book.get_cell_value("Sheet1", "A1"), CellErrorType.TYPE_ERROR)

    book.set_cell_contents("Sheet1", "A1", '=SUM(A1, 5)')
    assert is_error(book.get_cell_value("Sheet1", "A1"), CellErrorType.CIRCULAR_REFERENCE)

def test_SUM_circ_error_example():
    '''Test errors from calling own cell in range'''
    book = Workbook()
    book.new_sheet("Sheet1")
    book.set_cell_contents("Sheet1", "A1", '=SUM(A2:A4)')
    book.set_cell_contents("Sheet1", "A2", '1')
    book.set_cell_contents("Sheet1", "A3", '2')
    book.set_cell_contents("Sheet1", "A4", '=A1')


    assert is_error(book.get_cell_value("Sheet1", "A1"), CellErrorType.CIRCULAR_REFERENCE)
    assert is_error(book.get_cell_value("Sheet1", "A4"), CellErrorType.CIRCULAR_REFERENCE)

def test_MIN_typing():
    '''Test ordering of types'''
    book = Workbook()

    book.new_sheet("S")
    book.set_cell_contents("S", "A1", "=MIN(FALSE,0)")
    book.set_cell_contents("S", "B1", "=MIN(0, false)")
    assert book.get_cell_value('S', 'b1') == book.get_cell_value('S','a1')

    book.set_cell_contents("S", "c1", '=MIN("blue", "BLUE")')
    assert book.get_cell_value('S', 'c1') == "blue"

def test_AVERAGE():
    '''Test AVERAGE basics'''
    book = Workbook()
    book.new_sheet("Sheet1")


    book.set_cell_contents("Sheet1", "A1", '=AVERAGE(1,2,3)')
    assert book.get_cell_value("Sheet1", "A1") == 2

    book.set_cell_contents("Sheet1", "A1", '=AVERAGE(1, A2:A4)')
    assert book.get_cell_value("Sheet1", "A1") == 1/4

    book.set_cell_contents("Sheet1", "A1", '=AVERAGE(1, TRUE)')
    assert book.get_cell_value("Sheet1", "A1") == 1

    book.set_cell_contents("Sheet1", "A1", '=AVERAGE(1, "5")')
    assert book.get_cell_value("Sheet1", "A1") == 3

def test_AVERAGE_errors():
    '''Test errors from AVERAGE'''
    book = Workbook()
    book.new_sheet("Sheet1")

    book.set_cell_contents("Sheet1", "A1", '=AVERAGE(A2:A4)')
    assert is_error(book.get_cell_value("Sheet1", "A1"), CellErrorType.DIVIDE_BY_ZERO)

    book.set_cell_contents("Sheet1", "A1", '=AVERAGE()')
    assert is_error(book.get_cell_value("Sheet1", "A1"), CellErrorType.TYPE_ERROR)

    book.set_cell_contents("Sheet1", "A1", '=AVERAGE(1, "hello")')
    assert is_error(book.get_cell_value("Sheet1", "A1"), CellErrorType.TYPE_ERROR)

    book.set_cell_contents("Sheet1", "A1", '=AVERAGE(1, 1/0)')
    assert is_error(book.get_cell_value("Sheet1", "A1"), CellErrorType.TYPE_ERROR)

    book.set_cell_contents("Sheet1", "A1", '=AVERAGE(A1, 5)')
    assert is_error(book.get_cell_value("Sheet1", "A1"), CellErrorType.CIRCULAR_REFERENCE)

def test_HLOOKUP():
    '''Test HLOOKUP basics'''
    book = Workbook()
    book.new_sheet("Sheet1")


    book.set_cell_contents("Sheet1", "A1", '5')
    book.set_cell_contents("Sheet1", "A2", '1')
    book.set_cell_contents("Sheet1", "B1", "hello")
    book.set_cell_contents("Sheet1", "B2", '2')

    book.set_cell_contents("Sheet1", "A3", '=HLOOKUP(5, a1:a1,1)')
    assert book.get_cell_value("Sheet1", "A3") == 5

    book.set_cell_contents("Sheet1", "A3", '=HLOOKUP("hello", a1:b2,2)')
    assert book.get_cell_value("Sheet1", "A3") == 2

    book.set_cell_contents("Sheet1", "A3", '=HLOOKUP(5, a1:b2,2)')
    assert book.get_cell_value("Sheet1", "A3") == 1

    # Key doesn't exist
    book.set_cell_contents("Sheet1", "A3", '=HLOOKUP(-1, a1:b2,2)')
    assert is_error(book.get_cell_value("Sheet1", "A3"), CellErrorType.TYPE_ERROR)

    # Index out of range
    book.set_cell_contents("Sheet1", "A3", '=HLOOKUP(5, a1:b2, 3)')
    assert is_error(book.get_cell_value("Sheet1", "A3"), CellErrorType.TYPE_ERROR)

    # Circ ref
    book.set_cell_contents("Sheet1", "A3", '=HLOOKUP(5, A3:b2, 3)')
    assert is_error(book.get_cell_value("Sheet1", "A3"), CellErrorType.CIRCULAR_REFERENCE)

def test_VLOOKUP():
    '''Test VLOOKUP basics'''
    book = Workbook()
    book.new_sheet("Sheet1")

    book.set_cell_contents("Sheet1", "A1", '5')
    book.set_cell_contents("Sheet1", "A2", '1')
    book.set_cell_contents("Sheet1", "B1", "hello")
    book.set_cell_contents("Sheet1", "B2", '2')

    book.set_cell_contents("Sheet1", "A3", '=VLOOKUP(5, a1:a1,1)')
    assert book.get_cell_value("Sheet1", "A3") == 5

    book.set_cell_contents("Sheet1", "A3", '=VLOOKUP(1, a1:b2,2)')
    assert book.get_cell_value("Sheet1", "A3") == 2

    book.set_cell_contents("Sheet1", "A3", '=VLOOKUP(5, a1:b2,2)')
    assert book.get_cell_value("Sheet1", "A3") == "hello"

    # Key doesn't exist
    book.set_cell_contents("Sheet1", "A3", '=VLOOKUP(-1, a1:b2,2)')
    assert is_error(book.get_cell_value("Sheet1", "A3"), CellErrorType.TYPE_ERROR)

    # Index out of range
    book.set_cell_contents("Sheet1", "A3", '=VLOOKUP(5, a1:b2, 3)')
    assert is_error(book.get_cell_value("Sheet1", "A3"), CellErrorType.TYPE_ERROR)

    # Circ ref
    book.set_cell_contents("Sheet1", "A3", '=HLOOKUP(5, A3:b2, 3)')
    assert is_error(book.get_cell_value("Sheet1", "A3"), CellErrorType.CIRCULAR_REFERENCE)

def test_update_formula_rename_ranges():
    '''Test renames in ranges'''
    book = Workbook()
    book.new_sheet("S")

    book.set_cell_contents("s", "A1", "=SUM(B1:B5)")
    book.set_cell_contents("s", "A2", "=SUM(S!$B$1:B5)")
    book.set_cell_contents("s", "A3", "=SUM('S'!B1:B5)")
    book.set_cell_contents("s", "A4", '=INDIRECT("s!B1:B5")')

    book.rename_sheet("S", "S1")
    assert book.get_cell_contents("S1", "A1") == "=SUM(B1:B5)"
    assert book.get_cell_contents("S1", "A2") == "=SUM(S1!$B$1:B5)"
    assert book.get_cell_contents("S1", "A3") == "=SUM(S1!B1:B5)"
    #assert book.get_cell_contents("S1", "A4") == '=INDIRECT("S1!B1:B5")'

def test_update_formula_copy_cells():
    '''Test copy updates in ranges'''
    book = Workbook()
    book.new_sheet("S")

    book.set_cell_contents("s", "A1", "=SUM(B1:B5)")
    book.set_cell_contents("s", "A2", "=SUM(S!$B$1:B5)")
    book.set_cell_contents("s", "A3", "=SUM('S'!B1:B5)")
    book.set_cell_contents("s", "A4", "=SUM(B1:$B5)")
    book.set_cell_contents("s", "A4", "=SUM(B1:B$5)")

    book.copy_cells("S", "A1", "A4", "B1")
    assert book.get_cell_contents("S", "B1") == "=SUM(C1:C5)"
    assert book.get_cell_contents("S", "B2") == "=SUM(S!$B$1:C5)"
    assert book.get_cell_contents("S", "B3") == "=SUM('S'!C1:C5)"
    assert book.get_cell_contents("S", "B4") == "=SUM(C1:C$5)"

def test_existing_functions_cell_ranges():
    '''Test old functions with ranges'''
    book = Workbook()
    book.new_sheet("S")

    book.set_cell_contents("S", "C1", "5")
    book.set_cell_contents("S", "B1", "True")
    book.set_cell_contents("S", "A1", '=SUM(IF(B1, C1:C5, D1:D10))')
    assert book.get_cell_value("S", "A1") == 5

    book.set_cell_contents("S", "A1", '=SUM(CHOOSE("1", C1:C5, D1:D10))')
    assert book.get_cell_value("S", "A1") == 5

def test_existing_functions_cell_ranges_more():
    '''Test more complicated expressions from old functions'''
    book = Workbook()
    book.new_sheet("S")

    book.set_cell_contents("S", "C1", "5")

    book.set_cell_contents("S", "A1", '=SUM(INDIRECT(C1:C5))')
    assert book.get_cell_value("S", "A1") == 5

    book.set_cell_contents("S", "A1", '=SUM(INDIRECT("C1:C5"))')
    assert book.get_cell_value("S", "A1") == 5

    book.set_cell_contents("S", "A1", '=SUM(INDIRECT("C1" & ":C5"))')
    assert book.get_cell_value("S", "A1") == 5

    book.set_cell_contents("S", "A1", '=SUM(INDIRECT("S!"&"C1" & ":C5"))')
    assert book.get_cell_value("S", "A1") == 5

def test_sort_bad_input():
    '''Test errors with bad sorting inputs'''
    book = Workbook()
    book.new_sheet("S")

    with pytest.raises(KeyError):
        book.sort_region("a", "A1", "b5", [1,2,3])
    with pytest.raises(ValueError):
        book.sort_region("S", "A1", "b5", [1,2,-10])
    with pytest.raises(ValueError):
        book.sort_region("S", "A1", "b5", [1,2,-2])
    with pytest.raises(ValueError):
        book.sort_region("S", "A1", "b5", [1,2,3.5])

    with pytest.raises(ValueError):
        book.sort_region("S", "A1", "z99999", [1,2,3.5])

def test_sort_range():
    '''Test sorting basics'''
    book = Workbook()
    book.new_sheet("S")


    book.set_cell_contents("S", "A1", "1")
    book.set_cell_contents("S", "A2", "2")
    book.set_cell_contents("S", "A3", "True")
    book.set_cell_contents("S", "A4", "Hello")
    book.set_cell_contents("S", "A5", "=1/0")
    book.set_cell_contents("S", "A6", "=A6")

    book.sort_region("S", "A1", "b7", [-1,-2])


    assert book.get_cell_value("S", "A1")
    assert book.get_cell_value("S", "A2") == "Hello"
    assert book.get_cell_value("S", "A3") == 2
    assert book.get_cell_value("S", "A4") == 1
    assert is_error(book.get_cell_value("S", "A5"), CellErrorType.DIVIDE_BY_ZERO)
    assert is_error(book.get_cell_value("S", "A6"), CellErrorType.CIRCULAR_REFERENCE)
    assert book.get_cell_value("S", "A7") is None

def test_sort_range_neg():
    '''Test sorting in different order'''
    book = Workbook()
    book.new_sheet("S")


    book.set_cell_contents("S", "A1", "1")
    book.set_cell_contents("S", "A2", "2")
    book.set_cell_contents("S", "A3", "True")
    book.set_cell_contents("S", "A4", "Hello")
    book.set_cell_contents("S", "A5", "=1/0")
    book.set_cell_contents("S", "A6", "=A6")

    book.sort_region("S", "A1", "b7", [1,-2])


    assert book.get_cell_value("S", "A7")
    assert book.get_cell_value("S", "A6") == "Hello"
    assert book.get_cell_value("S", "A5") == 2
    assert book.get_cell_value("S", "A4") == 1
    assert is_error(book.get_cell_value("S", "A3"), CellErrorType.DIVIDE_BY_ZERO)
    assert is_error(book.get_cell_value("S", "A2"), CellErrorType.CIRCULAR_REFERENCE)
    assert book.get_cell_value("S", "A1") is None

def test_sort_range_mult_col():
    '''Test sort with multiple columns needed'''
    book = Workbook()
    book.new_sheet("S")

    book.set_cell_contents("S", "A1", "1")
    book.set_cell_contents("S", "A2", "1")
    book.set_cell_contents("S", "B1", "1")
    book.set_cell_contents("S", "B2", "2")


    book.sort_region("S", "A1", "b2", [-1,-2])
    assert book.get_cell_value("S", "B1") == 2
    assert book.get_cell_value("S", "B2") == 1


    book.sort_region("S", "A1", "b2", [-1,2])
    assert book.get_cell_value("S", "B1") == 1
    assert book.get_cell_value("S", "B2") == 2

    book.sort_region("S", "A1", "b2", [1,2])
    assert book.get_cell_value("S", "B1") == 1
    assert book.get_cell_value("S", "B2") == 2


def test_sort_range_mult_col_errors():
    '''Test sort with multiple columns needed'''
    book = Workbook()
    book.new_sheet("S")

    book.set_cell_contents("S", "A1", "=1/0")
    book.set_cell_contents("S", "A2", "=1/0")
    book.set_cell_contents("S", "B1", "1")
    book.set_cell_contents("S", "B2", "2")


    book.sort_region("S", "A1", "b2", [-1,-2])
    assert book.get_cell_value("S", "B1") == 2
    assert book.get_cell_value("S", "B2") == 1


    book.sort_region("S", "A1", "b2", [-1,2])
    assert book.get_cell_value("S", "B1") == 1
    assert book.get_cell_value("S", "B2") == 2

    book.sort_region("S", "A1", "b2", [1,2])
    assert book.get_cell_value("S", "B1") == 1
    assert book.get_cell_value("S", "B2") == 2

def test_sort_strings_only():
    book = Workbook()
    book.new_sheet("S")

    book.set_cell_contents("S", "A1", "'hello")
    book.set_cell_contents("S", "A2", "'Hello")
    book.set_cell_contents("S", "A3", "'a")
    book.sort_region("S", "A1", "b3", [1])

    # String comparisons are case insensitive, so stable sort is tested
    assert book.get_cell_value("S", "A1") == "a"
    assert book.get_cell_value("S", "A2") == "hello"
    assert book.get_cell_value("S", "A3") == "Hello"


def test_sort_errors_only():
    book = Workbook()
    book.new_sheet("S")

    book.set_cell_contents("S", "A1", "=1/0")
    book.set_cell_contents("S", "A2", "=SUM()")
    book.set_cell_contents("S", "A3", "=non!A5")
    book.set_cell_contents("S", "A4", "=A4")
    book.set_cell_contents("S", "A5", "=#")

    book.sort_region("S", "A1", "a5", [1])
    assert is_error(book.get_cell_value("S", "A1"), CellErrorType.PARSE_ERROR)
    assert is_error(book.get_cell_value("S", "A2"), CellErrorType.BAD_NAME)
    assert is_error(book.get_cell_value("S", "A3"), CellErrorType.TYPE_ERROR)
    assert is_error(book.get_cell_value("S", "A4"), CellErrorType.CIRCULAR_REFERENCE)
    assert is_error(book.get_cell_value("S", "A5"), CellErrorType.DIVIDE_BY_ZERO)



def test_sort_range_mult_col_stable():
    '''Test sorting is stable'''
    book = Workbook()
    book.new_sheet("S")
    book.set_cell_contents("S", "A1", "1")
    book.set_cell_contents("S", "A2", "1")
    book.set_cell_contents("S", "B1", "1")
    book.set_cell_contents("S", "B2", "2")
    book.sort_region("S", "A1", "b2", [1])

    assert book.get_cell_value("S", "B1") == 1
    assert book.get_cell_value("S", "B2") == 2


def test_sort_range_update_form():
    '''Test sort with references'''
    book = Workbook()
    book.new_sheet("S")
    book.set_cell_contents("S", "A1", "=B1")
    book.set_cell_contents("S", "A2", "=B2")
    book.set_cell_contents("S", "B1", "1")
    book.set_cell_contents("S", "B2", "2")

    book.sort_region("S", "A1", "A2", [-1])

    assert book.get_cell_value("S", "A1") == 1
    assert book.get_cell_value("S", "A2") == 2

def test_sort_range_cell_ref():
    '''Test updates based on changes in sorting'''
    book = Workbook()
    book.new_sheet("S")

    book.set_cell_contents("S", "A1", "1")
    book.set_cell_contents("S", "A2", "2")
    book.set_cell_contents("S", "B1", "1")
    book.set_cell_contents("S", "B2", "2")

    # Other cell that references cells in sorted region
    book.set_cell_contents("S", "C1", "= A1")

    book.sort_region("S", "A1", "b2", [-1])
    assert book.get_cell_value("S", "A1") == 2
    assert book.get_cell_value("S", "A2") == 1
    assert book.get_cell_value("S", "C1") == 2

changed = set([])
def on_cells_changed(_workbook, changed_cells):
    '''
    This function gets called when cells change in the workbook that the
    function was registered on.  The changed_cells argument is an iterable
    of tuples; each tuple is of the form (sheet_name, cell_location). It simply
    add the liustof changed_cells to the changed global set.
    '''
    global changed
    changed = changed_cells
    changed.sort()

def test_notify_cell_update_move():
    '''notify simple update moving'''
    global changed
    changed = set([])
    workbook = Workbook()
    workbook.notify_cells_changed(on_cells_changed)
    (_index, name) = workbook.new_sheet("Sheet1")
    workbook.set_cell_contents(name, "a1", "5")
    workbook.set_cell_contents(name, "a2", "10")
    workbook.set_cell_contents(name, "a3", "FALSE")
    workbook.set_cell_contents(name, "a4", "'boof")
    workbook.set_cell_contents(name, "a5", "'tough")
    workbook.move_cells(name, "a1", "a5", "b2")

    cells = [("Sheet1", "A1"),("Sheet1", "A2"),("Sheet1", "A3"),("Sheet1", "A4"),
        ("Sheet1", "A5"),("Sheet1", "B2"),("Sheet1", "B3"),("Sheet1", "B4"),
        ("Sheet1", "B5"),("Sheet1", "B6")]
    cells.sort()
    assert cells == changed

def test_notify_cell_update_copy():
    '''notify simple update copying'''
    global changed
    changed = set([])
    workbook = Workbook()
    workbook.notify_cells_changed(on_cells_changed)
    (_index, name) = workbook.new_sheet("Sheet1")
    workbook.set_cell_contents(name, "a1", "5")
    workbook.set_cell_contents(name, "c1", "8")
    workbook.set_cell_contents(name, "b1", "=a1+c1")
    workbook.copy_cells(name, "a1", "a1", "c1")

    cells = [("Sheet1", "C1"),("Sheet1", "B1")]
    cells.sort()
    assert cells == changed

def test_notify_cell_update_rename():
    '''notify simple update renaming'''
    global changed
    changed = set([])
    workbook = Workbook()
    workbook.notify_cells_changed(on_cells_changed)
    (_index, _name) = workbook.new_sheet("Sheet1")
    (_index, _name) = workbook.new_sheet("Sheet2")
    workbook.set_cell_contents("Sheet1", "a1", "5")
    workbook.set_cell_contents("Sheet1", "a2", "=A1")
    workbook.set_cell_contents("Sheet2", "a2", "=renamed!A1")
    assert is_error(workbook.get_cell_value("Sheet2", "A2"), CellErrorType.BAD_NAME)
    cells = [("Sheet2", "A2")]
    workbook.rename_sheet("Sheet1", "renamed")
    assert workbook.get_cell_value("Sheet2", "a2") == 5
    assert cells == changed

def test_notify_cell_update_sort():
    '''notify simple update sorting'''
    global changed
    changed = set([])
    book = Workbook()
    book.notify_cells_changed(on_cells_changed)
    book.new_sheet("S")

    book.set_cell_contents("S", "A1", "1")
    book.set_cell_contents("S", "A2", "2")
    book.set_cell_contents("S", "A3", "True")
    book.set_cell_contents("S", "A4", "Hello")
    book.set_cell_contents("S", "A5", "=1/0")
    book.set_cell_contents("S", "A6", "=A6")

    book.sort_region("S", "A1", "b7", [1,-2])

    cells = [("S", "A1"),("S", "A2"),("S", "A3"),("S", "A4"),("S", "A5"),
    ("S", "A6"),("S", "A7")]
    cells.sort()
    assert cells == changed
