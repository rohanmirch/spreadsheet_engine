'''sheet class'''
from .cell import get_cell_tuple
class Sheet:
    '''Represents the sheets in the Workbook'''
    def __init__(self, name):
        self.name = name
        self.cells = {}

    def get_extent(self):
        '''get extent of sheet'''
        tuples = \
        [get_cell_tuple(c) for c in self.cells if self.cells[c].value is not None]
        if tuples:
            unzipped = list(zip(*tuples))
            return(max(unzipped[0]), max(unzipped[1]))
        return (0,0)
