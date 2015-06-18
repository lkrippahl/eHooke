# Module used to store the images and the different masks

class Image:
    # Class used to store the phase and fluorescence images and the different masks needed

    def __init__(self, params):

        self.phase_image = None
        self.base_mask = None
        self.phase_mask = None
        self.fluorescence_image = None

    def load_phase(self):
        pass

    def load_fluorescence(self):
        pass

    def save_image(self):
        pass

    def compute_base_mask(self):
        pass

    def compute_phase_mask(self):
        pass
