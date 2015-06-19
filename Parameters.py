# Module used to store the parameters used in the different phases of the software

import numpy as np


class Parameters:

    def __init__(self):
        self.imageloaderparams = ImageLoaderParameters()
        self.imageprocessingparams = ImageProcessingParameters()
        self.generatereportparams = GenerateReportParameters()

    def load_parameters(self):
        pass

    def save_parameters(self):
        pass

class ImageLoaderParameters:

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


class ImageProcessingParameters:

    def __init__(self):
        pass

class GenerateReportParameters:

    def __init__(self):
        pass
