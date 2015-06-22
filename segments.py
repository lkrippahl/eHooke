# Module used to process the images: region labeling, cell finding and cell stats computing

class Cell:

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

    def __init__(self):
        pass
