"""Encapsulate eHooke processor
   ----------------------------
   
   This model provides the EHooke class which encapsulates all processing

   It also provides the run_ehooke function which allows an EHooke object
   to be run in an independent process

"""

from masks import Mask
from frames import FrameManager
from params import Parameters
from skimage.io import imsave, imread

class EHooke(object):
    """Encapsulates all the code for processing a set of images"""

    def __init__(self,params_obj=None,param_file=None):
        """Creates FrameManager object, sets up parameters and loads images

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
            
        self.frames = FrameManager()
        """FrameManager: manager for the value and mask pairs"""

    def init_frames(self, images):
        """initialise the frame manager with thelisted images
        """

        fparams = self.params.frame_params
        self.frames.initialise(fparams,images)
        

    def create_masks(self,compute_all = False):
        """creates masks using the current parameters
           computes only current frame by default.
        """
        
        mparams = self.params.mask_params
        self.frames.create_masks(mparams,compute_all)

    def align_to_mask(self, compute_all = False):
        """aligns the fluorescence image to the phase mask, if a phase file exists"""
        
        frames.align_to_mask(self.params.fluor_frame_params)


    def save_mask_overlay(self, fname, back=(0,0,1), fore=(1,1,0), mask='phase',image='phase'):
        """saves the mask overlay image to a file"""    

        img = self.frames.mask_overlay(back, fore, mask,image)
        imsave(fname,img)

    def save_mask_contour(self, fname, mask='phase',image='phase', color=(1,1,0)):
        """saves the mask contour image to a file"""    

        img = self.frames.contour_overlay(mask,image,color)
        imsave(fname,img)

EH_TERMINATE = '**term**'
"""str: command for terminating a ehooke process"""

def run_ehooke(conn,params,images):
    """run ehooke as a separate process

       Arg:
       conn is a connection to parent process from where commands are retrieved
           each command is a tuple of a command string (a method of EHooke) and
           the arguments as a dictionary
       params is the parameters object to pass to the EHooke instance
       images is the image dictionary for initializing EHooke
    """
    ehooke = EHooke(params)
    ehooke.init_frames(images)
    while True:
        fn,args = conn.recv()        
        if fn == EH_TERMINATE:
            return
        else:
            method = getattr(ehooke,fn)
            res = method(**args)
            if res is not None:
                conn.send(res)
            
