"""Module used to store the images and the different masks

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

    def compute_phase_mask(self, base_mask, params):
        """computes the phase mask from precomputed base mask """

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

    

class FluorFrame:
    """A fluorescence microscopy frame

    Loads exactly one fluorescence microscopy image and, optionally, one phase contrast image
    Also manages the masks for defining the cell regions
    
    """

    def __init__(self):
        """just clears all variables and creates the Mask objects"""

        self.clip = (0, 0, 0, 0)
        """tuple: specifies which part of the images to use """
        self.phase_image = None
        """ndarray: the phase image, if used present. Otherwise fluorescence image should be used for mask"""
        self.fluor_image = None
        """ndarray: the fluorescence image, mandatory"""        
        self.fluor_baseline = None
        """float: baseline for fluorescence measurements"""

        self.base_mask = Mask()
        """Mask: the base mask, obtained from thresholding the parent image"""        
        self.phase_mask = Mask()
        """Mask: obtained from the base_mask plus binary closing"""   
        

    def get_clip(self, margin):
        """returns the clipping region to the fuor image minus the margin on each side"""

        lx, ly = self.fluor_image.shape
        return (margin, margin, lx-margin, ly-margin)

    def load_phase(self, params):
        """loads phase image and converts it to grayscale as float

        params is a FluorFrameParameters object with the parameters for loading the phase

        """

        self.phase_image = img_as_float(imread(params.phase_file))
        self.phase_image = exposure.rescale_intensity(self.phase_image)  # rescales the intensity of the phase image
        self.phase_image = color.rgb2gray(self.phase_image)

        if params.invert_phase:
            self.phase_image = 1 - self.phase_image        

    def load_fluor(self, params):
        """loads the fluorescence image and converts it if == RGB
           sets the clip rectangle
        """
    
        self.fluor_image = imread(params.fluor_file,as_grey=True)        
        self.clip = self.get_clip(params.phase_border)

    def align_fluor(self, params):
        """aligns fluorescence image to phase mask
        """

        clip = self.clip
        width = params.align_margin
        #reset clipping if alignment margin is larger
        if params.phase_border<params.align_margin:
            width = params.phase_border

        minscore = 0        
        best = (0, 0)
        x1, y1, x2, y2 = clip
        mask = self.phase_mask.mask
        for dx in range(-width, width):
            for dy in range(-width, width):
                total = -np.sum(np.multiply(mask, self.fluor_image[x1+dx:x2+dx, y1+dy:y2+dy]))
                if total < minscore:
                    minscore = total
                    best = (dx, dy)

        dx, dy = best        

    def compute_fluor_baseline(self, params):
        """computes the baseline for fluorescence"""
        
        dilated_mask = morphology.dilation(mask,morphology.disc(params.baseline_margin))
        self.fluor_baseline = np.average(np.multiply(dilated_mask, self.fluor_image))

        
    def clear_masks(self):
        """Disposes of masks and sets them to None """
        if self.base_mask is not None:
            self.base_mask.dispose()
        if self.phase_mask is not None:
            self.phase_mask.dispose()
        self.base_mask = None
        self.phase_mask = None
        

    def create_masks(self,mask_parameters,create_phase=True):
        """creates the base mask and the phase mask
            base_mask has no hole filling or closing
            phase mask background is white, cells are black"""

        self.clear_masks()        
        x1, y1, x2, y2 = self.clip
        self.base_mask = Mask()
        if self.phase_image is None:
            self.base_mask.compute_base_mask(self.fluor_image[x1:x2,y1:y2],mask_parameters)            
        else:
            self.base_mask.compute_base_mask(self.phase_image[x1:x2,y1:y2],mask_parameters)
            
        if create_phase:
            self.phase_mask = Mask()
            self.phase_mask.compute_phase_mask(self.base_mask.mask,mask_parameters)

    def mask_image_pair(self,mask='base',image='phase'):
        """returns a tuple of ndmatrices, (mask, image), with the selected combination"""

        x1, y1, x2, y2 = self.clip
        
        if mask=='base':
            amask=self.base_mask.mask
        else:
            amask=self.phase_mask.mask

        if image=='phase':
            aimage=self.phase_image[x1:x2,y1:y2]
        else:
            aimage=self.fluor_image[x1:x2,y1:y2]
        return (amask,aimage)

    def mask_overlay(self, back, fore, mask='base',image='phase'):        
        """returns an RGB image of the image multiplied by back outside the mask
           and by fore inside the mask.

           back and fore are triples with color intensities e.g (1,0,0) (1,1,0) for red and yellow
        """
        amask,aimage = self.mask_image_pair(mask,image)
        res = None
        if amask is not None and aimage is not None:            
            w, h = amask.shape
            res = np.empty((w, h, 3), dtype=np.float)
            res[:,:,0] = (1-amask) * back[0] * aimage + amask * fore[0] * aimage
            res[:,:,1] = (1-amask) * back[1] * aimage + amask * fore[1] * aimage
            res[:,:,2] = (1-amask) * back[2] * aimage + amask * fore[2] * aimage
            
        return res
        

    def contour_overlay(self,mask='base',image='phase', color=(1,1,0)):        
        """overlays a mask with an image
           The mask can be 'base' or 'phase'
           The image can be 'flur' or 'phase'
        """
        amask,aimage = self.mask_image_pair(mask,image)

        res = None
        if amask is not None and aimage is not None:            
            res = mark_boundaries(aimage,amask,color = color, outline_color=None)
        return res
