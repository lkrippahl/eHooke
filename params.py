"""Module used to store the parameters used in the different phases of the software"""

import numpy as np


class Parameters:

    def __init__(self):
        self.imageloaderparams = MaskParameters()
        self.imageprocessingparams = RegionParameters()
        self.generatereportparams = CellParameters()

    def load_parameters(self):
        pass

    def save_parameters(self):
        pass

class MaskParameters:

    def __init__(self):

        # phase image parameters
        self.phase_file = ""  # margin removed from phase, at least as much as fluorescence phase parameter
        self.phase_border = 10  # phase file, including path
        self.invert_phase = False
        # if true, phase will be inverted. Useful when using fluorescence or light on dark background

        self.mask_algorithms = ['Local Average', 'Absolute']
        self.mask_algorithm = 'Local Average'

        # used for local average algorithm
        self.mask_blocksize = 100  # block size for moving average
        self.mask_offset = 0.02    # offset for moving average

        # used for absolute threshold algorithm
        self.absolute_threshold = 0.6  # cutoff value for background

        # used as mask creation parameters
        self.mask_fill_holes = False  # fill holes in enclosed regions, useful if cells are not uniform dark blobs
        self.mask_closing = np.ones((5, 5))  # matrix for removing white and black spots, if empty no removal
        self.mask_dilation = 0  # mask dilation iterations

        # fluorescence image parameters
        self.fluor_file = ''  # fluorescence file, including path
        self.align_margin = 10  # margin for searching fluorescence
        self.phase_is_fluorescence = False  # if true then fluorescence is the image used for phase, without processing


class RegionParameters:

    def __init__(self):

        # cell identification parameters
        self.identification_algorithms = ['Distance Peak', 'Feature Label']
        self.identification_algorithm = 'Distance Peak'

        # axis computation parameters
        self.axis_algorithms = ['Box', 'Septum']
        self.axis_algorithm = 'Box'
        self.axial_step = 5         # angular step in degrees

        # distance peak parameters
        self.peak_min_distance = 10
        self.peak_min_height = 5
        self.peak_max_height = 20
        self.peak_min_distance_from_edge = 30
        self.max_peaks = 1000

        # feature labelling parameters
        self.outline_use_base_mask = False     # assign fixed height to all in base mask
        self.outline_base_mask_depth = 5      # height to assign basemask

class CellParameters:

    def __init__(self):

        # cell filtering criteria
        self.cell_filters = [('Area', 150, 700), ('Neighbours', 0, 2)]
        self.cells_forced = []
        self.cells_excluded = []

        # cell merging parameters
        self.cell_force_merge_below = 0
        self.merge_dividing_cells = True
        self.merge_length_tolerance = 1.1
        self.merge_min_interface = 15

        # cell mask for brightness
        self.inner_mask_thickness = 5

        # margin for local baseline
        self.baseline_margin = 30

        # display
        self.cell_colors = 10
