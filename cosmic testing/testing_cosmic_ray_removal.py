# -*- coding: utf-8 -*-
"""
Created on Mon Jan 19 14:01:23 2015

@author: dreadnought

"Brevity required, prurience preferred"
"""

from __future__ import division
import numpy as np
import json
import matplotlib.pyplot as plt
import cosmics_hsg as cosmics

class EMCCDimage(object):
    
    def __init__(self, file_name):
        '''
        This does the load text file for you, and reads the header to put the
        appropriate values in the correct place
        It will try to open an already-cleaned version of the background image,
        called <BG_image_name>_clean.txt
        
        '''
        self.fname = file_name
        
        f = open(file_name,'rU')
            
        self.description = f.readline()
        self.description = self.description[1:]
        #self.parameters = json.loads(f.readline())
        f.close()
        
        self.raw_array = np.genfromtxt(file_name, comments='#', delimiter=',')
        self.raw = self.raw_array.T

    def clean_up(self, mygain, myreadnoise=3.0, mysigclip=5.0, mysigfrac=0.5, myobjlim=5.0, myverbose=True):
        '''
        This is a single operation of cosmic ray removal.

        If EMCCD isn't cold enough, the hot pixels wil be removed as well.  I 
        don't know if this is a bad thing?  I think it should just be a thing
        that doesn't happen.
        
        my_array = the array you want to clean
        myreadnoise = Level (imprecise!) of read noise used in the statistical
                      model built to recognize cosmic arrays.  It's a function
                      of gain on our CCD, I believe.  Dark current should be 
                      separate, technically, but it would look like noise 
                      because of shot noise and crap
        mysigclip = I forget
        mysicfrac = I forget
        myobjlim = I forget
        myverbose = Tells hsg_cosmics to print out what it's doing
        
        
        Here's from the actual file:
        sigclip : increase this if you detect cosmics where there are none. Default is 5.0, a good value for earth-bound images.
        objlim : increase this if normal stars are detected as cosmics. Default is 5.0, a good value for earth-bound images.
        
        Constructor of the cosmic class, takes a 2D numpy array of your image as main argument.
        sigclip : laplacian-to-noise limit for cosmic ray detection 
        objlim : minimum contrast between laplacian image and fine structure image. Use 5.0 if your image is undersampled, HST, ...
        
        satlevel : if we find agglomerations of pixels above this level, we consider it to be a saturated star and
        do not try to correct and pixels around it. A negative satlevel skips this feature.
        
        pssl is the previously subtracted sky level !
        
        real   gain    = 1.8          # gain (electrons/ADU)    (0=unknown)
        real   readn   = 6.5              # read noise (electrons) (0=unknown)
        ##gain0  string statsec = "*,*"       # section to use for automatic computation of gain
        real   skyval  = 0.           # sky level that has been subtracted (ADU)
        real   sigclip = 3.0          # detection limit for cosmic rays (sigma)
        real   sigfrac = 0.5          # fractional detection limit for neighbouring pixels
        real   objlim  = 3.0           # contrast limit between CR and underlying object
        int    niter   = 1            # maximum number of iterations    
        '''
        image_removal = cosmics.cosmicsimage(self.raw_array, mygain, # I don't understand gain
                                             readnoise=myreadnoise, 
                                             sigclip=mysigclip, 
                                             sigfrac=mysigfrac, 
                                             objlim=myobjlim)
        image_removal.run(maxiter=4)
        self.clean = image_removal.cleanarray.T
        self.mask = image_removal.mask.T*1000
    
    def integrate(self):
        '''
        Integrates over vertical axis of the cleaned image
        '''
        self.hsg_signal = self.clean_array[:,self.y_min:self.y_max].sum(axis=1)

    
    def append_wavelengths(self):
        '''
        This appends the appropriate wavelengths for self.hsg_signal to make 
        np.array([wavelengths, self.hsg_signal]).
        
        Wait until after all the manipulation of the data before doing this?
        '''
        wavelengths = gen_wavelengths(self.center, self.grating)
        self.hsg_data = np.concatenate((wavelengths, self.hsg_signal)).reshape(2,1600).T
    
    def save_arrays(self, file_name):
        '''
        This will save the raw, clean and mask arrays
        '''
        np.savetxt(file_name + '.txt', np.vstack((self.raw, self.clean, self.mask)))

def gen_wavelengths(center_lambda, grating):
    '''
    This returns a 1600 element list of wavelengths for each pixel in the EMCCD based on grating and center wavelength
    
    grating = which grating, 1 or 2
    center = center wavelength in nanometers
    '''
    b = 0.75
    k = -1.0
    r = 16.0e-6

    if grating == 1:
        d = 1./1800000.
        gamma = 0.2243885861015487
        delta = 1.353959952416065
    elif grating == 2:
        d = 1./1200000.
        gamma = 0.2207676478674860
        delta = 1.352055027245235
    else:
        print "What a dick, that's not a valid grating"
        return None
    
    center = center_lambda*10**-9
    wavelength_list = np.arange(-799.0,801.0)
    
    output = d*k**(-1)*((-1)*np.cos(delta+gamma+(-1)*np.arccos((-1/4)*(1/np.cos((1/2)*gamma))**2*(2*(np.cos((1/2)*gamma)**4*(2+(-1)*d**(-2)*k**2*center**2+2*np.cos(gamma)))**(1/2)+d**(-1)*k*center*np.sin(gamma)))+np.arctan(b**(-1)*(r*wavelength_list+b*np.cos(delta+gamma))*(1/np.sin(delta+gamma))))+(1+(-1/16)*(1/np.cos((1/2)*gamma))**4*(2*(np.cos((1/2)*gamma)**4*(2+(-1)*d**(-2)*k**2*center**2+2*np.cos(gamma)))**(1/2)+d**(-1)*k*center*np.sin(gamma))**2)**(1/2))   
    
    output = (output + center)*10**9
    return output

test = EMCCDimage('longExposures43.txt')
test.clean_up(1, myreadnoise=5.0, mysigclip=5.5, mysigfrac=0.3, myobjlim=3.0)
test.save_arrays('crr43')