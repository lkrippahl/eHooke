"""Module used to compute value image baseline
  
   
"""

import numpy as np

class Baseline(object):
    """Computes and provides baseline values for value images"""

    def __init__(self, value_image):
        # TODO implement everything
        # <LK 2015-07-27>
        # baseline margin in BaselineParams
        # polynomial background baseline: http://stackoverflow.com/questions/7997152/python-3d-polynomial-surface-fit-order-dependent
        #
        self.bl_values = None

    
