'''Test time of renaming a sheet'''
import context
from sheets import Workbook
from pyinstrument import Profiler

if __name__ == '__main__':

    wb = Workbook()
    p = Profiler()

    wb.new_sheet("Sheet1")
    wb.new_sheet("Sheet2")

    for n in range(1, 1001):
        wb.set_cell_contents("Sheet1", "A{}".format(n), "=A{}".format(n+1))
        wb.set_cell_contents("Sheet2", "A{}".format(n), "=Sheet1!A{}".format(n))

    p.start()
    wb.rename_sheet("Sheet1", "renamed")
    p.stop()

    print(p.output_text(unicode=True, color=True))
