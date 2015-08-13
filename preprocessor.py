"""Manages image preprocessing

   (called when loading images)  

"""

from skimage.io import imread

def load_image(file_name,frame_params):
    """Loads value image and does preprocessing if any"""
    print file_name

    if frame_params.preprocess:
        raise NotImplementedError('Preprocessing not implemented')
        # TODO Implement denoising
        # <LK 2015-08-04>
    else:
        return imread(file_name,as_grey=True)
    
