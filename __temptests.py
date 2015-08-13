"""quick and dirty testing, not supposed to go to repository"""

import masks
import params
import numpy as np
from skimage.io import imsave, imread
from skimage.filter import threshold_otsu,threshold_yen


def test_mask(ff,out_image,offset,save_all=False):
    m_params = params.MaskParameters()
    m_params.offset=offset
    m_params.absolute_threshold=offset
    m_params.algorithm='lala'
    ff.create_masks(m_params)

    if save_all:
        imsave(out_image+'_base_phase.png',ff.overlay('base','phase'))
        imsave(out_image+'_phase_phase.png',ff.overlay('phase','phase'))
        imsave(out_image+'_phase.png',ff.phase_image)
        
    imsave(out_image+'_base.png',ff.phase_mask.mask)



ff_params= params.FluorFrameParameters()
ff = masks.FluorFrame(ff_params)
filename = 'Images/1hOxa_1_w1Phase.TIF'
ff.load_phase(filename)    
thresholds=np.arange(0.15,0.2,0.01)

for thresh in thresholds:
    test_mask(ff,'pngs/test'+str(thresh),thresh,True)
    
