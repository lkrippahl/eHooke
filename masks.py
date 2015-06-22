"""Module used to store the images and the different masks"""

from skimage.io import imsave, imread
from skimage.util import img_as_float
from skimage import exposure, color, morphology, filters
import numpy as np
from scipy import ndimage

from params import Parameters  # remove after testing


class Image:
    """Class used to store the phase and fluorescence images and the different masks needed"""

    def __init__(self, parameters):

        self.imageloaderparams = parameters
        self.clip = (0, 0, 0, 0)
        self.phase_image = None
        self.base_mask = None
        self.phase_mask = None
        self.fluorescence_image = None
        self.fluorescence_baseline = None
        self.cells = []  # used to store the cells objects created by the imageprocessing module

    def clear_all(self):
        self.phase_image = None
        self.base_mask = None
        self.phase_mask = None
        self.fluorescence_image = None
        self.cells = []

    def set_clip(self, margin):
        """sets the clipping region to the image minus the margin on each side"""

        lx, ly = self.phase_image.shape
        self.clip = (margin, margin, lx-margin, ly-margin)

    def load_phase(self, filename):
        """loads phase image and converts it to grayscale as float"""

        self.phase_image = img_as_float(imread(filename))
        self.phase_image = exposure.rescale_intensity(self.phase_image)  # rescales the intensity of the phase image
        self.phase_image = color.rgb2gray(self.phase_image)

        if self.imageloaderparams.invert_phase:
            self.phase_image = 1 - self.phase_image

        self.set_clip(self.imageloaderparams.phase_border)

    def load_fluorescence(self, filename):
        """loads the fluorescence image and converts it if == RGB"""

        fluor_image = imread(filename)

        if len(fluor_image.shape) > 2:
            fluor_image = color.rgb2gray(fluor_image)

        minscore = 0
        width = self.imageloaderparams.align_margin
        best = (0, 0)
        x1, y1, x2, y2 = self.clip
        inverted_mask = 1 - self.phase_mask

        if not self.imageloaderparams.phase_is_fluorescence:
            for dx in range(-width, width):
                for dy in range(-width, width):
                    total = -np.sum(np.multiply(inverted_mask, fluor_image[x1+dx:x2+dx, y1+dy:y2+dy]))

                    if total < minscore:
                        minscore = total
                        best = (dx, dy)

        dx, dy = best
        self.fluorescence_image = fluor_image[x1+dx:x2+dx, y1+dy:y2+dy]
        self.fluorescence_baseline = np.average(np.multiply(self.phase_mask, self.fluorescence_image))

    def save_image(self, filename, image_to_save):
        imsave(filename, image_to_save)

    def compute_base_mask(self):
        """creates the base mask for the phase image without hole filling or closing
        background is white, cells are black"""

        x1, y1, x2, y2 = self.clip
        base_mask = np.copy(self.phase_image[x1:x2, y1:y2])

        if self.imageloaderparams.mask_algorithm == "Local Average":
            base_mask = filters.threshold_adaptive(base_mask, self.imageloaderparams.mask_blocksize,
                                                   offset=self.imageloaderparams.mask_offset)
        else:
            outs = base_mask > self.imageloaderparams.absolute_threshold
            ins = base_mask < self.imageloaderparams.absolute_threshold
            base_mask[outs] = 1
            base_mask[ins] = 0

        self.base_mask = base_mask

    def compute_phase_mask(self):
        """computes the phase_mask using the base mask
        computes the edges using the clipping region and the parameters"""

        self.compute_base_mask()
        phase_mask = self.base_mask

        if len(self.imageloaderparams.mask_closing) > 0:
            phase_mask = morphology.closing(phase_mask, self.imageloaderparams.mask_closing)  # removes small dark spots
            phase_mask = 1-img_as_float(morphology.closing(1-img_as_float(phase_mask),
                                                           self.imageloaderparams.mask_closing))  # removes small white spots

        if self.imageloaderparams.mask_fill_holes:
            phase_mask = 1-img_as_float(ndimage.binary_fil_holes(1.0-phase_mask))  # mask is inverted

        for f in range(self.imageloaderparams.mask_dilation):
            # previous code used self.mask before assigning it
            phase_mask = morphology.erosion(phase_mask, np.ones((3, 3)))

        self.phase_mask = img_as_float(phase_mask)
