'''Test dependencies for a large number of children'''
import context
from sheets import Workbook
from pyinstrument import Profiler

if __name__ == '__main__':

    wb = Workbook()
    p = Profiler()

    wb.new_sheet("sheet1")
    wb.set_cell_contents("sheet1", "A1", "=1")

    for n in range(2, 1001):
        wb.set_cell_contents("sheet1", "A{}".format(n), "=1+A1")

    p.start()
    wb.set_cell_contents("sheet1", "A1", "20")
    p.stop()

    print(p.output_text(unicode=True, color=True))
