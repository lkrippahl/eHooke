"""Generate and store masks

   IMPORTANT: mask convention is that regions of interest (e.g. cells) are marked with 1 and
   background is 0. If phase images have black cells in light background the mask must be inverted

"""

from skimage.io import imsave, imread
from skimage.util import img_as_float
from skimage import exposure, color, morphology, filter
import numpy as np
from scipy import ndimage
from skimage.segmentation import mark_boundaries
from skimage.filter import threshold_isodata
from baseline import Baseline
from params import MaskParameters 

class Mask:
    """Masks are binary images representing regions of interest of a parent image

    CONVENTIONS: foreground is assumed to be darker than background and set to value 1
                 If otherwise set the invert mask parameter to True.

    This class is responsible for
        Generating the base_mask, which is simply the thresholding of the parent mask
        Generating the phase_mask from a base mask, which is the base_mask plus binary closing            
        Computing mask statistics

    
    """
    
    def __init__(self):
        """Sets mask to None
        """
        
        self.mask = None    
        """ndarray: mask matrix, without closing"""
        

    def compute_base_mask(self,image,params):
        """Creates the base mask for the phase image

           params is a MaskParameters object with the necessary parameters
        """
        
        self.mask = np.copy(image)

        if params.auto_threshold:
            params.absolute_threshold = threshold_isodata(self.mask)

        if params.algorithm == "Local Average":
            #need to invert because threshold_adaptive sets dark parts to 0
            self.mask = 1.0-filter.threshold_adaptive(self.mask, params.blocksize,offset=params.offset)
        else:
            if params.auto_threshold:
                params.absolute_threshold = threshold_isodata(self.mask)
            #the convention is that dark is foreground and with mask set to 1            
            self.mask = img_as_float(image <= params.absolute_threshold)
            
        if params.invert:
            self.invert_mask()

    def compute_final_mask(self, base_mask, params):
        """computes the final mask from precomputed base mask """

        self.mask = np.copy(base_mask)
        
        if params.closing > 0:            
            # removes small dark spots and then small white spots
            closing_disk = morphology.disk(params.closing)
            self.mask = img_as_float(morphology.closing(self.mask, closing_disk))
            self.mask = 1-img_as_float(morphology.closing(1-self.mask, closing_disk))

        if params.fill_holes:
            self.mask = img_as_float(ndimage.binary_fil_holes(self.mask)) 

        if params.dilation > 0:
            dilation_disk = morphology.disk(params.dilation)
            self.mask = morphology.dilation(self.mask, dilation_disk)

        #self.mask = img_as_float(phase_mask)
            #FIXME This is either unnecessary or something is wrong
            #test it and fix it <LK 2015-06-27>

    def invert_mask(self):
        """the mask is 0 on dark regions and 1 on light regions.
           If the background is light and we want to use 1 to set the ROI, then the mask must be inverted           
        """

        self.mask = 1.0 - self.mask
    
    def dispose(self):
        """Cleanup objects that this class may create"""
        self.mask = None

    

