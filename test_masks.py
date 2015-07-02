import unittest
import masks
import params

class MaskTestCase(unittest.TestCase):
    def setUp(self):
        self.mask = masks.Mask()

    def tearDown(self):
        self.mask.dispose()        
        self.mask = None

    def test_mask_parameters(self):
        """Tests if mask parameters are all adequately set and retrieved
           and are not changed by the mask object"""
        # TODO create a set of parameters, set those parameters, run
        # image generation etc and check if the parameters are the same
        # <LK 2015-06-27>
        
    def test_create_mask(self):
        """Tests mask creation algorithms"""
        # TODO create sample images (matrices of 0 with other values) and
        # check if the mask has the right number of pixels set to 1
        # <LK 2015-06-27>


def suite():
    "Test suite"
    suite1 = unittest.TestLoader().loadTestsFromTestCase(MaskTestCase)
    # add other suites here
    return unittest.TestSuite([suite1])  #and add them to this list too

unittest.TextTestRunner(verbosity=2).run(suite())
    
