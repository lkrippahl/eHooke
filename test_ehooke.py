import unittest
import ehooke
import params

class MaskTestCase(unittest.TestCase):
    def setUp(self):
        self.params = params.Parameters()
        self.params.fluor_frame_params.phase_file = 'Images/1hOxa_1_w1Phase.TIF'
        self.params.fluor_frame_params.fluor_file = 'Images/1hOxa_1_w1Phase.TIF'        
        self.ehooke = ehooke.EHooke(self.params)

    def tearDown(self):
        self.ehooke = None
        self.params = None

    def test_overlay(self):
        """Tests loading fluor, phase, making masks and overlays"""
        
        self.ehooke.load_images()
        self.ehooke.save_mask_overlay('Images/overlay.png', back=(0,0,1), fore=(1,1,0), mask='phase',image='phase')
        self.ehooke.save_mask_contour('Images/contour.png', mask='phase',image='phase')

def suite():
    "Test suite"
    suite1 = unittest.TestLoader().loadTestsFromTestCase(MaskTestCase)
    # add other suites here
    return unittest.TestSuite([suite1])  #and add them to this list too

unittest.TextTestRunner(verbosity=2).run(suite())
    
