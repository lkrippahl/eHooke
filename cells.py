"""Module used to process the cell regions of the cell

Uses the regions defined by the segments.py and accert if they correspond to cells based on the parameters

"""

class Cell:
    """class used to store the attributes of every cell"""

    def __init__(self):

        self.cell_mask = None
        self.perimeter_mask = None
        self.septum_mask = None

    def compute_cell_mask(self):
        pass

    def compute_perimeter_mask(self):
        pass

    def compute_septum_mask(self):
        pass

class ImageCells:
    """class used to store every cell belonging to the image"""

    def __init__(self):
        pass
