'''Test a lot of small circular dependencies'''
import context
from sheets import Workbook
from pyinstrument import Profiler

if __name__ == '__main__':

    wb = Workbook()
    p = Profiler()

    wb.new_sheet("Sheet1")

    for n in range(2, 1001):
        wb.set_cell_contents("Sheet1", "A{}".format(n), "=B{} + A1".format(n))
        wb.set_cell_contents("Sheet1", "B{}".format(n), "=A{}".format(n))

    p.start()
    wb.set_cell_contents("Sheet1", "A1", "10")
    p.stop()

    print(p.output_text(unicode=True, color=True))
