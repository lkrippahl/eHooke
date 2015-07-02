"""Main module of the software, used to run the program"""

from masks import Mask,FluorFrame
from params import Parameters
from skimage.io import imsave, imread

class EHooke:
    """Encapsulates all the code for processing a fluorescence frame"""

    def __init__(self,params_obj=None,param_file=None):
        """Creates FluorFrame object, sets up parameters and loads images

           It makes no sense to create a EHooke object without data or parameters.
           So one must either supply params, a Parameters object, or param_file, in
           which case EHooke loads the parameters file.
        """

        self.params = None
        """Parameters: this can be a reference to an external object to be
           changed for recomputing any step.
        """

        if params_obj is None:
            self.params = Parameters()
            self.params.load_parameters(param_file)
        else:
            self.params = params_obj
            
        self.fluor_frame = FluorFrame()
        """FluorFrame: manager for the fluor and phase images, plus masks"""

    def load_images(self):
        """checks which images to load and loads them into the fluor_frame
        """
           

        ffparams = self.params.fluor_frame_params
        self.fluor_frame.load_fluor(ffparams)
        if ffparams.phase_file is not None:
            self.fluor_frame.load_phase(ffparams)

    def create_masks(self):
        """creates masks using the current parameters"""
        
        mparams = self.params.mask_params
        self.fluor_frame.create_masks(mparams)

    def align_fluor_to_phase(self):
        """aligns the fluorescence image to the phase mask, if a phase file exists"""
        
        if ffparams.phase_file is not None:
            self.fluor_frame.align_fluor(self.params.fluor_frame_params)


    def save_mask_overlay(self, fname, back=(0,0,1), fore=(1,1,0), mask='phase',image='phase'):
        """saves the mask overlay image to a file"""    

        img = self.fluor_frame.mask_overlay(back, fore, mask,image)
        imsave(fname,img)

    def save_mask_contour(self, fname, mask='phase',image='phase', color=(1,1,0)):
        """saves the mask contour image to a file"""    

        img = self.fluor_frame.contour_overlay(mask,image,color)
        imsave(fname,img)


