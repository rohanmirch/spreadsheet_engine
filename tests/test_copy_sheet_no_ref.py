'''Test copying a sheet'''
import context
from sheets import Workbook
from pyinstrument import Profiler

if __name__ == '__main__':

    wb = Workbook()
    p = Profiler()

    wb.new_sheet("Sheet1")

    for n in range(1, 1001):
        wb.set_cell_contents("Sheet1", "A{}".format(n), "{}".format(n + 1))

    p.start()
    wb.copy_sheet("Sheet1")
    p.stop()

    print(p.output_text(unicode=True, color=True))
