'''Test loading in JSON'''
import context
from sheets import Workbook
from pyinstrument import Profiler
import io

if __name__ == '__main__':

    wb = Workbook()
    wb.new_sheet("Sheet1")
    wb.set_cell_contents("Sheet1", "A1", "=1")

    for n in range(2, 1001):
        wb.set_cell_contents("Sheet1", "A{}".format(n),
            "=A{}".format(n - 1))

    with io.StringIO() as filep:
        wb.save_workbook(filep)
        filep.seek(0)

        p = Profiler()

        p.start()
        wb = Workbook.load_workbook(filep)
        p.stop()

    print(p.output_text(unicode=True, color=True))
