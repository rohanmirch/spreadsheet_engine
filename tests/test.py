'''smoke Test Sheets package'''
import context
from sheets import Workbook
import sheets
#import sheets


# Should print the version number of your sheets library,
# which should be 1.0 for the first project.
print(f'Using sheets engine version {sheets.version}')


book = Workbook()
book.new_sheet("S")

book.set_cell_contents("S", "A1", "=1/0")
book.set_cell_contents("S", "A2", "=SUM()")
book.set_cell_contents("S", "A3", "=non!A5")
book.set_cell_contents("S", "A4", "=A4")
book.set_cell_contents("S", "A5", "=#")

book.sort_region("S", "A1", "a5", [1])
print(book.get_cell_value("S", "A1"))
print(book.get_cell_value("S", "A2"))
print(book.get_cell_value("S", "A3"))
print(book.get_cell_value("S", "A4"))
print(book.get_cell_value("S", "A5"))

#book.set_cell_contents("S", "A1", '=SUM(INDIRECT("C1" & ":C5"))')
#assert book.get_cell_value("S", "A1") == 5
