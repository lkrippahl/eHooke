"""Manages image frames (pairs of value image and mask image)
    

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
from masks import Mask
from params import FrameParameters
from preprocessor import load_image


class ImageFrame:
    """A value - mask image pair microscopy frame

    Loads exactly one value image and, optionally, one image for generating the mask
    Also manages the masks for defining the cell regions and aligns if necessary
    
    """

    def __init__(self):
        """just clears all variables and creates the Mask objects
        """

        self.clip = (0, 0, 0, 0)
        """tuple: specifies which part of the images to use """
        self.mask_image = None
        """ndarray: the image to be used as a mask. If absent, the value_image is used"""
        self.value_image = None
        """ndarray: the image used to measure values, this is mandatory"""
        self.base_mask = Mask()
        """Mask: the base mask, obtained from thresholding the parent image"""        
        self.final_mask = Mask()
        """Mask: obtained from the base_mask plus binary closing and other processing"""

        self.last_frame_params = -1
        """integer: value of last frame parameter changes. If lower than last_change value
           on frame parameters, means it's necessary to reload and recompute"""

        self.last_mask_params = -1
        """integer: value of last mask parameter changes. If lower than lasg_change value on
           mask parameters, must recompute mask"""

        self.value_file = None
        self.mask_file = None
        """string: files used for value and mask images"""
        

    def get_clip(self, margin):
        """returns the clipping region to the fuor image minus the margin on each side
        """

        lx, ly = self.value_image.shape
        return (margin, margin, lx-margin, ly-margin)

    def _load_mask(self, frame_params, mask_file):
        """loads mask image and converts it to grayscale as float
            
            This method should not be called from outside the load_images function so as not to lose
            track of parameter changes
        """
        self.mask_file = mask_file
        self.mask_image = img_as_float(imread(mask_file))
        self.mask_image = exposure.rescale_intensity(self.mask_image)  # rescales the intensity of the phase image
        self.mask_image = color.rgb2gray(self.mask_image)

        if frame_params.invert_mask_image:
            self.mask_image = 1 - self.mask_image        

    def _load_value(self, frame_params, value_file,mask_file):
        """loads the value image and converts it if == RGB
           sets the clip rectangle
           
           This method should not be called from outside the load_images function so as not to lose
           track of parameter changes
        """

        self.value_file = value_file
        self.value_image = load_image(self.value_file,frame_params)
        self.mask_image = mask_file
        self.clip = self.get_clip(frame_params.clipping_margin)            
        if mask_file is not None:
            self._load_mask(frame_params,mask_file)        

    def load_images(self,frame_params,value_file,mask_file):
        """loads value and mask images, updates frame params changes
        """
        self._load_value(frame_params,value_file,mask_file)
        self.last_frame_params = frame_params.last_change
        self.clear_masks()

    def align_value(self, params):
        """aligns fluorescence image to base mask
        """

        clip = self.clip
        width = params.align_margin
        #reset clipping if alignment margin is larger
        if params.phase_border<params.align_margin:
            width = params.phase_border

        minscore = 0        
        best = (0, 0)
        x1, y1, x2, y2 = clip
        mask = self.base_mask.mask
        for dx in range(-width, width):
            for dy in range(-width, width):
                total = -np.sum(np.multiply(mask, self.value_image[x1+dx:x2+dx, y1+dy:y2+dy]))
                if total < minscore:
                    minscore = total
                    best = (dx, dy)
        dx, dy = best
        self.clip = (x1+dx,y1+dy,x2+dx,y2+dy)
        

    def compute_value_baseline(self, params):
        """computes the baseline for fluorescence"""
        # TODO this should not be here. baseline is only for stats computations
        # <LK 2015-07-27>
        dilated_mask = morphology.dilation(mask,morphology.disc(params.baseline_margin))
        self.fluor_baseline = np.average(np.multiply(dilated_mask, self.value_image))

        
    def clear_masks(self):
        """Disposes of masks and sets them to None """
        if self.base_mask is not None:
            self.base_mask.dispose()
        if self.final_mask is not None:
            self.final_mask.dispose()
        self.base_mask = None
        self.final_mask = None
        

    def create_masks(self,mask_parameters,create_final=True):
        """creates the base mask and the phase mask
            base_mask has no hole filling or closing
            phase mask background is white, cells are black"""

        self.clear_masks()        
        x1, y1, x2, y2 = self.clip
        self.base_mask = Mask()
        if self.mask_image is None:
            self.base_mask.compute_base_mask(self.value_image[x1:x2,y1:y2],mask_parameters)            
        else:
            self.base_mask.compute_base_mask(self.mask_image[x1:x2,y1:y2],mask_parameters)
            
        if create_final:
            self.final_mask = Mask()
            self.final_mask.compute_final_mask(self.base_mask.mask,mask_parameters)
        self.last_mask_params = mask_parameters.last_changed

    def mask_image_pair(self,mask='base',image='mask'):
        """returns a tuple of ndmatrices, (mask, image), with the selected combination"""

        x1, y1, x2, y2 = self.clip
        
        if mask=='base':
            amask=self.base_mask.mask
        else:
            amask=self.final_mask.mask

        if image=='mask':
            aimage=self.mask_image[x1:x2,y1:y2]
        else:
            aimage=self.value_image[x1:x2,y1:y2]
        return (amask,aimage)

    def mask_overlay(self, back, fore, mask='base',image='mask'):        
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
        

    def contour_overlay(self,mask='base',image='mask', color=(1,1,0)):        
        """overlays a mask with an image
           The mask can be 'base' or 'phase'
           The image can be 'flur' or 'phase'
        """
        amask,aimage = self.mask_image_pair(mask,image)

        res = None
        if amask is not None and aimage is not None:            
            res = mark_boundaries(aimage,amask,color = color, outline_color=None)
        return res

    def update(self,frame_params,mask_params,index):
        """Compares changes in params and frame and mask last computation, reloading
           as necessary"""
        if frame_params.last_changed>self.last_frame_params:            
            self.load_images(frame_params,index)
            self.last_mask_param=-1
        if mask_params.last_changed>self.mask_params:
            self.create_masks(mask_params)
            
        

class FrameManager:
    """ Handles a set of frame images """

    def __init__(self):
        self.frames = []
        """"list: list of ImageFrame"""
        self.current_frame = None
        """ImageFrame: the frame currently in use, default for computations
        """
        self.images = {}
        """dictionary: value images as keys and masks as values, or None"""
        
    def initialise(self,frame_params,images):
        """Load all images in files, creating frames
           images is a dictionary with value image as keys and
           mask image (or None) as values
        """
        # IDEA Intelligent check for which frames need to be loaded
        # (use mask_file and value_file frame
        # <LK 2015-08-27>
        self.frames = []
        self.images = dict(images)
        for val_file in images.keys():
            frame = ImageFrame()
            frame.load_images(frame_params,val_file,images[val_file])
            self.frames.append(frame)
        if len(self.frames)>0:
            self.current_frame = self.frames[0]
        else:
            self.current_frame = None

    def create_masks(self,mask_params, compute_all = False):
        """creates masks using the given parameters
           computes only current frame by default.
        """

        if compute_all:
            for frame in self.frames:
                frame.create_masks(mask_params)
        else:
            self.current_frame.create_masks(mask_params)

    def mask_overlay(self, back, fore, mask='base',image='mask'):
        """return current_frame mask_overlay
        """
        return self.current_frame.mask_overlay(self, back, fore, mask, image)        
        

    def contour_overlay(self,mask='base',image='mask', color=(1,1,0)):
        """return current_frame contour_overlay
        """
        return rself.current_frame.contour_overlay(self,mask ,image , color)

    
