'''Test fib situation from email'''
import context
from sheets import Workbook
from pyinstrument import Profiler

if __name__ == '__main__':

    wb = Workbook()
    p = Profiler()

    # Make new sheet
    wb.new_sheet("Sheet1")
    #wb.set_cell_contents("Sheet1", "A1", "=1")
    wb.set_cell_contents("Sheet1", "A2", "1")

    for n in range(3, 1001):
        wb.set_cell_contents("Sheet1", "A{}".format(n),
            "=A{} + A{}".format(n - 1, n-2))

    p.start()
    wb.set_cell_contents("Sheet1", "A1", "1")
    p.stop()

    print(p.output_text(unicode=True, color=True))
