# Module used to store the images and the different masks

class Image:
    # Class used to store the phase and fluorescence images and the different masks needed

    def __init__(self, params):

        self.phase_image = None
        self.phase_mask = None
        self.fluorescence_image = None

    def compute_phase_mask(self):
        pass
