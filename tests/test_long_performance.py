'''Test long chain updates'''
import context
from sheets import Workbook
from pyinstrument import Profiler

if __name__ == '__main__':

    wb = Workbook()
    p = Profiler()

    # Make new sheet
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("Sheet1", "A1", "=1")

    for n in range(2, 1001):
        wb.set_cell_contents("Sheet1", "A{}".format(n),
            "=A{}".format(n - 1))

    p.start()
    wb.set_cell_contents("Sheet1", "A1", "10")
    p.stop()

    print(p.output_text(unicode=True, color=True))
