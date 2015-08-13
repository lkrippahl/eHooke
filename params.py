"""Module used to store the parameters used in the different phases of the software"""

import numpy as np
import ConfigParser as cp


class BaseParameters(object):
    """Base class for specific parameters"""
    exported = []
    """List of tuples with names and labels of attributes that are to be
       exported to the user"""

    def __init__(self):
        self.last_change = 0
        """Integer value keeping track of last parameter changes to help
           determine what needs to be recomputed"""
        

class MaskParameters(BaseParameters):
    """Stores, loads and saves parameters for generating masks
    Also generates a default set of parameters"""

    exported = [('algorithm','Mask algorithm'),
                ('blocksize','Block size (local)'),
                ('offset','Offset (local)'),
                ('absolute_threshold','Threshold (absolute)'),
                ('auto_threshold','Automatic threshold'),
                ('fill_holes','Fill mask holes'),
                ('closing','Radius of closing'),
                ('dilation','Radius of dilation'),
                ('invert','Invert mask')]
    """List of tuples with names and labels of attributes that are to be
       exported to the user"""

    
    def __init__(self):
        super(MaskParameters, self ).__init__()
        self.algorithms = ['Local Average', 'Absolute']
        """list of acceptable algorithms for mask generation"""
        #FIXME: perhaps this should be a class attribute <LK 2015-2-7>
        
        self.algorithm = 'Absolute'
        
        # local average
        self.blocksize = 100           # block size for moving average
        self.offset = 0.0              # offset for moving average

        # absolute
        self.absolute_threshold = 0.2  # cutoff value for background
        self.auto_threshold = True     # compute threshold with isodata

        #postprocessing
        self.fill_holes = False        # fill holes in enclosed regions, useful if cells are not uniform dark blobs
        self.closing = 3               # radius of disk used for removing white and black spots, if 0 no removal
        self.dilation = 0              # mask dilation iterations
        self.invert = False            # False for default of black shapes on white background

    def load_from_parser(self,parser,section):
        """Loads mask parameters from a ConfigParser object of the configuration file
           The section parameters specifies the configuration file section
        """

        self.fill_holes = parser.getboolean(section, 'mask_fill_holes')
        self.blocksize = parser.getint(section, 'mask_blocksize')
        self.offset = parser.getfloat(section, 'mask_offset')
        self.absolute_threshold = parser.getfloat(section, 'absolute_threshold')
        self.auto_threshold = parser.getboolean(section, 'auto_threshold')
        tmp = parser.get(section, 'mask_algorithm')
        if tmp in self.algorithms:
            self.algorithm = tmp
        else:
            self.algorithm = self.algorithms[0]              
        self.closing = parser.getint(section, 'mask_closing')
        self.invert = parser.getboolean(section, 'mask_invert')

    def save_to_parser(self,parser,section):
        """Saves mask parameters to a ConfigParser object of the configuration file
           It creates the section if it does not exist.
        """
        if section not in parser.sections():
            parser.add_section(section)
        parser.set(section, 'mask_blocksize', self.blocksize)
        parser.set(section, 'mask_offset', self.offset)
        parser.set(section, 'mask_algorithm', self.algorithm)
        parser.set(section, 'absolute_threshold', self.absolute_threshold)
        parser.set(section, 'auto_threshold', self.auto_threshold)
        parser.set(section, 'mask_fill_holes', self.fill_holes)
        parser.set(section, 'mask_closing', self.closing)
        parser.set(section, 'mask_dilation', self.dilation)
        parser.set(section, 'mask_invert', self.invert)

        
class BaselineParameters(BaseParameters):
    """Parameters for computing value image baseline
       Used for cell statistics
    """

    def __init__(self):
        super(BaselineParameters, self ).__init__()
        self.baseline_margin = 20
        """int: number of pixels away from mask where fluorescence baseline is computed"""
   

class FrameParameters(BaseParameters):
    """Stores parameters for the image frames

    These are parameters that, if changed, require reloading all images and recomputing from zero
    """

    def __init__(self):
        super(FrameParameters, self ).__init__()
        
        # mask image parameters
        self.invert_mask_image = False
        """bool: if true, mask image will be inverted.
                 Useful when using value as mask or light on dark background"""
        
        # value image parameters
        self.clipping_margin = 10
        """int: margin removed from images, at least as much as align_margin parameter if phase is used"""        

        self.align_margin = 10
        """int: margin for aligning with mask image if a mask image is used.
                is overriden by clipping_margin if clipping_margin is smaller
        """
        
        self.preprocess = False
        """Boolean: if true, do preprocessing"""
        
    def load_from_parser(self,parser,section):
        """Loads frame parameters from a ConfigParser object of the configuration file
           The section parameters specifies the configuration file section
        """
                
        self.clipping_margin = parser.getint(section, 'clipping_margin')        
        self.invert_mask_image = parser.getboolean(section, 'invert_mask_image')
        self.align_margin = parser.getint(section, 'align_margin')
        self.preprocess = parser.getboolean(section, 'preprocess')
        
        
    def save_to_parser(self,parser,section):
        """Saves frame parameters to a ConfigParser object of the configuration file
           It creates the section if it does not exist.
        """
        if section not in parser.sections():
            parser.add_section(section)
        parser.set(section, 'invert_phase', self.invert_phase)
        parser.set(section, 'clipping_margin', self.phase_border)
        parser.set(section, 'align_margin', self.align_margin)
        parser.set(section, 'preprocess', self.preprocess)        
      

class SegmentationParameters(BaseParameters):

    def __init__(self):
        super(SegmentationParameters, self ).__init__()
        
       

class ReportParameters(BaseParameters):

    def __init__(self):
        super(ReportParameters, self ).__init__()
        

    
class Parameters:

    def __init__(self):
        self.mask_params = MaskParameters()
        self.frame_params = FrameParameters()
        # TODO implement the other parameters
        # <LK 2015-06-27>        
        #self.imageprocessingparams = ImageProcessingParameters()
        #self.generatereportparams = GenerateReportParameters()

    def load_parameters(self,filename):
        """Loads parameters from a configuration file"""
        
        parser = cp.ConfigParser()
        parser.read(filename)
        self.mask_params.load_from_parser(parser,'Mask')
        self.frame_params.load_from_parser(parser,'Frame')
        # TODO implement loading for the other parameters
        # <LK 2015-06-27>
        

    def save_parameters(self,filename):
        """Saves parameters from a configuration file"""
        
        parser = cp.ConfigParser()
        self.mask_params.save_to_parser(parser,'Mask')
        self.frame_params.save_to_parser(parser,'Frame')
        # TODO implement loading for the other parameters
        # <LK 2015-06-27>
        cfgfile = open(filename,'w')
        parser.write(cfgfile)
        cfgfile.close()

    
