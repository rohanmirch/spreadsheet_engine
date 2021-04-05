''' Test circular references in a long chain'''
import os
import sys
from pyinstrument import Profiler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sheets import Workbook


if __name__ == '__main__':

    wb = Workbook()
    p = Profiler()

    wb.new_sheet("Sheet1")

    for n in range(2, 1001):
        wb.set_cell_contents("Sheet1", "A{}".format(n), "=A{}".format(n-1))

    p.start()
    wb.set_cell_contents("Sheet1", "A1", "=A9999")
    p.stop()

    print(p.output_text(unicode=True, color=True))
