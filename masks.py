"""Module used to store the images and the different masks
   IMPORTANT: mask convention is that regions of interest (e.g. cells) are marked with 1 and
   background is 0. If phase images have black cells in light background the mask must be inverted
"""

from skimage.io import imsave, imread
from skimage.util import img_as_float
from skimage import exposure, color, morphology, filter
import numpy as np
from scipy import ndimage

from params import MaskParameters  # remove after testing


class Image:
    """A fluorescence microscopy frame
    Loads exactly one fluorescence microscopy image and, optionally, one phase contrast image
    Also manages the masks for defining the cell regions
    Masks are binary images representing regions of interest of a parent image
    CONVENTIONS: foreground is assumed to be darker than background and set to value 1
    If otherwise set the invert mask parameter to True.
    The mask class stores a reference to the parent image but does not copy it
    """

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
        """Clears every object that this class has created"""

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
        """Creates the base mask for the phase image
        image is the original image, set in self.phase_image
        """

        x1, y1, x2, y2 = self.clip
        base_mask = np.copy(self.phase_image[x1:x2, y1:y2])

        if self.imageloaderparams.mask_algorithm == "Local Average":
            base_mask = filter.threshold_adaptive(base_mask, self.imageloaderparams.mask_blocksize,
                                                  offset=self.imageloaderparams.mask_offset)
        else:
            outs = base_mask > self.imageloaderparams.absolute_threshold
            ins = base_mask < self.imageloaderparams.absolute_threshold
            base_mask[outs] = 1
            base_mask[ins] = 0

        self.base_mask = base_mask

    def compute_phase_mask(self):
        """computes the phase mask
           the phase mask is computed from a given base mask
        """

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

    def invert_mask(self):
        """the mask is 0 on dark regions and 1 on light regions.
           If the background is light and we want to use 1 to set the ROI, then the mask must be inverted
        """

        self.phase_mask = 1.0 - self.phase_mask

    def overlay(self, mask="base", image="phase"):
        """overlays a mask with an image
           The mask can be 'base' or 'phase'
           The image can be 'fluor' or 'phase'
        """

        if mask == 'base':
            amask = self.base_mask
        else:
            amask = self.phase_mask

        if image == 'phase':
            aimage = self.phase_image
        else:
            aimage = self.fluor_image

        if amask is not None and aimage is not None:
            x1, y1, x2, y2 = self.clip
            return amask.mask * aimage[x1:x2, y1:y2]
