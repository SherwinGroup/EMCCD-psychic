# -*- coding: utf-8 -*-
"""
Created on Mon Jan 19 14:01:23 2015

@author: dreadnought

"Brevity required, prurience preferred"
"""

from __future__ import division
import os, errno
import copy
import json
import numpy as np
import matplotlib.pyplot as plt
import cosmics_hsg as cosmics

class EMCCD_image(object):
    
    def __init__(self, raw_array, file_name, description, equipment_dict):
        '''
        This init is to work with the most basic images with no specialiation
        for HSG or PL or absorbance data.  Feels like we should have something
        more general than those.
        
        raw_array = the CCD image with the pertinent data
        bg_array = the CCD image with the pertinent backgroud data
        description = string that contains a brief description of the file
        equipment_dict = dictionary that contains the important settings of the
                         equipment:
                             CCD_temperature = temp of CCD chip
                             exposure = exposure time
                             gain = EM gaine
                             y_min = lower boundary of ROI
                             y_max = upper boundary of ROI
                             grating = spectrometer grating
                             center_lambda = spectrometer wavelength setting
                             slits = width of slits in microns
                             dark_region (maybe not that useful if can look at y_max + n) 
                             bg_file_name = name of background file
							 series = name for series
        '''
        self.raw_array = np.array(raw_array)
        self.raw_shape = self.raw_array.shape
        self.file_name = file_name
        self.description = description
        self.equipment_dict = equipment_dict
        if self.equipment_dict['y_max'] - self.equipment_dict['y_min'] > int(self.raw_shape[0]):
            print "y_min and y_max were set incorrectly"
            self.equipment_dict['y_max'] = int(self.raw_shape[0]) - 1
            self.equipment_dict['y_min'] = 0
        self.clean_array = None
        self.spectrum = None
        self.addenda = [0, file_name] # This is important for keeping track of addition and subtraction
        self.subtrahenda = []

    def __str__(self):
        '''
        This will print the description of the file.  I'm not sure what else
        would be useful at this time.
        '''
        return self.description
    
    def __add__(self, other):
        '''
        This will copy the first element in the sum, then add the clean_arrays
        from self and other to each other.  It can also currently add an int or
        float to the clean_array.  I'm not sure if that kind of addition is 
        useful.
        
        The center_lambda check needs to be changed to match how that 
        dictionary entry works.  It could get ugly without double checking.
        '''
        if self.clean_array is None:
            raise Exception('Source: EMCCD_image.__add__\nThe first array has not been cleaned yet')
        ret = copy.deepcopy(self)
        
        # Add a constant offset to the data
        if type(other) in (int, float):
            ret.clean_array = self.clean_array + other
            ret.addenda[0] = ret.addenda[0] + other
        
        # or add the two clean_arrays together
        else:
            if np.isclose(ret.equipment_dict['center_lambda'], 
                          other.equipment_dict['center_lambda']):
                ret.clean_array = self.clean_array + other.clean_array
                ret.addenda[0] = ret.addenda[0] + other.addenda[0]
                ret.addenda.extend(other.addenda[1:])
                ret.subtrahenda.extend(other.subtrahenda)
            else:
                raise Exception('Source: EMCCD_image.__add__\nThese are not from the same grating settings')
        return ret

    def __sub__(self, other):
        '''
        This subtracts constants or other data sets between self.hsg_data.  I 
        think it even keeps track of what data sets are in the file and how 
        they got there.  
        
        The center_lambda check needs to be changed to match how that 
        dictionary entry works.  It could get ugly without double checking.
        '''
        if self.clean_array is None:
            raise Exception('Source: EMCCD_image.__sub__\nThe first array has not been cleaned yet')
        ret = copy.deepcopy(self)
        
        if type(other) in (int, float):
            ret.clean_array = self.clean_array - other
            ret.addenda[0] = ret.addenda[0] - other
        else:
            if np.isclose(ret.equipment_dict['center_lambda'], 
                          other.equipment_dict['center_lambda']):
                ret.clean_array = self.clean_array - other.clean_array
                ret.addenda[0] = ret.addenda[0] - other.addenda[0]
                ret.subtrahenda.extend(other.addenda[1:])
                ret.addenda.extend(other.subtrahenda)
            else:
                raise Exception('Source: EMCCD_image.__sub__\nThese are not from the same grating settings')
        return ret
        
    def __getslice__(self, *args):
        print 'getslice ', args
        #Simply pass the slice along to the data
        return self.spectrum[args[0]:args[1]]
        
    def __iter__(self):
        for i in range(len(self.spectrum)):
            yield self.spectrum[i]
        return
    
    def set_ylimits(self, y_min, y_max):
        '''
        This changes y_min and y_max
        '''
        self.equipment_dict['y_min'] = y_min
        self.equipment_dict['y_max'] = y_max
    
    def cosmic_ray_removal(self, mygain=1, myreadnoise=3.0, mysigclip=5.0, mysigfrac=0.3, myobjlim=3.0, myverbose=True):
        '''
        This is a single operation of cosmic ray removal.

        If EMCCD isn't cold enough, the hot pixels wil be removed as well.  I 
        don't know if this is a bad thing?  I think it should just be a thing
        that doesn't happen.
        
        mygain = the gain.  This does not seem to actually be the EM gain of 
                 the EMCCD
        myreadnoise = Level (imprecise!) of read noise used in the statistical
                      model built to recognize cosmic arrays.  It's a function
                      of gain on our CCD, I believe.  Dark current should be 
                      separate, technically, but it would look like noise 
                      because of shot noise and crap
        mysigclip = I forget
        mysicfrac = I forget
        myobjlim = I forget
        myverbose = Tells hsg_cosmics to print out what it's doing
        
        returns a clean my_array
        '''
        
#        self.clean_array = self.raw_array
#        return
        image_removal = cosmics.cosmicsimage(self.raw_array, gain=mygain, # I don't understand gain
                                             readnoise=myreadnoise, 
                                             sigclip=mysigclip, 
                                             sigfrac=mysigfrac, 
                                             objlim=myobjlim)
        image_removal.run(maxiter=4)
        self.clean_array = image_removal.cleanarray
    
    def make_spectrum(self):
        '''
        Integrates over vertical axis of the cleaned image
        
        I'm not exactly sure y_min and y_max are counting from the same side as
        in the UI.
        '''
        self.spectrum = self.clean_array[:,self.equipment_dict['y_min']:self.equipment_dict['y_max']].sum(axis=1)        
        wavelengths = gen_wavelengths(self.equipment_dict['center_lambda'], 
                                      self.equipment_dict['grating'])
        self.spectrum = np.concatenate((wavelengths, self.spectrum)).reshape(2,1600).T
        
    def inspect_dark_regions(self):
        '''
        This will look at a dark area, I'm not quite sure how yet, to make sure
        the mean is set to zero.  It will also measure the standard deviation 
        of the noise for use later.
        '''
        dark_region = self.clean_array[:,0] # This is a total kludge
        self.dark_mean = np.mean(dark_region)
        self.std_dev = np.std(dark_region)
        print "Base line is ", self.dark_mean
        print "Standard deviation is ", self.std_dev
        height = self.equipment_dict['y_max'] - self.equipment_dict['y_min']
        self.spectrum[:,1] = self.spectrum[:, 1] - self.dark_mean*height
        self.addenda[0] += self.dark_mean*height
    
    def save_spectrum(self, folder_str='Spectrum files'):
        '''
        Saves the general spectrum.  Unsure if we need it, but, again, seems
        useful for novel, basic stuff.
        '''

        self.equipment_dict['addenda'] = self.addenda
        self.equipment_dict['subtrahenda'] = self.subtrahenda
        equipment_str = json.dumps(self.equipment_dict, sort_keys=True)
        origin_import = '\nWavelength,Signal\nnm,arb. u.'
        filename = self.file_name + "_spectrum.txt"
        my_header = '#' + equipment_str + '#' + self.description + '\n' + origin_import
        np.savetxt(os.path.join(folder_str, filename), self.spectrum,
                   delimiter=',', header=my_header, comments = '', fmt='%f')
    
    def save_images(self, folder_str='Raw files'):
        '''
        Saves the raw_array, not the cleaned one.  Cleaning isn't that hard, 
        and how we do it could change in the future.
        
        This really depends on how the folders are initialized by the UI.  Will
        they already exist by the time we get to saving images, or do they need
        to be created on the fly?
        
        Also, I'm pretty sure self.raw_array is still ints?
        '''
        print 'adding dict'
        self.equipment_dict['addenda'] = self.addenda
        self.equipment_dict['subtrahenda'] = self.subtrahenda
        print 'json dumping'
        try:
            equipment_str = json.dumps(self.equipment_dict, sort_keys=True)
        except:
            print "Source: EMCCD_image.save_images\nJSON FAILED"
            print self.equipment_dict
            return
        
        my_header = equipment_str + '\n' +  self.description
        
        filename = self.file_name + '.txt'

        print 'saving'
        try:
            print os.path.join(folder_str, self.file_name)
        except:
            print "Source: EMCCD_image.save_images\nospath failed"
        try:
            np.savetxt(os.path.join(folder_str, filename), self.raw_array,
                   delimiter=',', header=my_header, comments = '#', fmt='%d')
        except Exception as e:
            print e
            print "Source: EMCCD_image.save_images"
            print 'type: {}'.format(type(self.raw_array))
            print 'size: {}'.format(self.raw_array.size)



class HSG_image(EMCCD_image):
    '''
    This subclass will specialize in HSG initializing and saving, which mostly
    has to do with what the header in the file is at this point.  
    '''
    
    def __init__(self, raw_array, file_name, description, hsg_dict, equipment_dict):
        '''
        This takes the image array, the appropriate bg_array, and two dicts to 
        create the object that turn into the spectrum that will be saved.
        
        image_array = 400x1600 array with data in it
        bg_array = appropriate bg_array
        hsg_dict = the important parameters for hsg: 
            sample_name
            sample_temperature
            NIR_power
            NIR_lambda
            THz_power (or field, or intensity, whatever is easiest)
            THz_freq (best guess from FEL calculations, not from sidebands)
            num_FEL_shots (hopefully counted from teh 'scope)
            series
        equipment_dict = the important nonspecific conditions:
            CCD_temperature
            exposure
            gain
            y_min
            y_max
            grating
            center_lambda
            slits
            dark_region (maybe not that useful if can look at y_max + n)
        
        Other things to init:
        self.addenda = list that keeps track of constant offset
        self.background_name = name of appropriate background
        '''
        self.raw_array = np.array(raw_array)
        self.file_name = file_name
        self.description = description
        self.hsg_dict = hsg_dict
        self.equipment_dict = equipment_dict
        self.clean_array = None
        self.spectrum = None
        self.addenda = [0, file_name] # This is important for keeping track of addition and subtraction
        self.subtrahenda = []

    def save_spectrum(self, folder_str='HSG files'):
        '''
        Saves the general spectrum.  Unsure if we need it, but, again, seems
        useful for novel, basic stuff.
        '''
        try:
            os.mkdir(folder_str)
        except OSError, e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise
        
        hsg_str = json.dumps(self.hsg_dict)
        self.equipment_dict['addenda': self.addenda]
        self.equipment_dict['subtrahenda': self.subtrahenda]
        equipment_str = json.dumps(self.equipment_dict, sort_keys=True)
        
        save_file_name = 'hsg_' + self.file_name
        origin_import = '\nWavelength,Signal\nnm,arb. u.'
        my_header = self.description + '\n' + hsg_str + '\n' + equipment_str + origin_import
        np.savetxt(os.path.join(folder_str, save_file_name), self.spectrum, 
                   delimiter=',', header=my_header, comments='#', fmt='%f')

    def save_images(self, folder_str='Raw files'):
        '''
        Saves the raw_array, not the cleaned one.  Cleaning isn't that hard, 
        and how we do it could change in the future.
        
        This really depends on how the folders are initialized by the UI.  Will
        they already exist by the time we get to saving images, or do they need
        to be created on the fly?
        
        Also, I'm pretty sure self.raw_array is still ints?
        '''
        try:
            os.mkdir(folder_str)
        except OSError, e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise
        
        hsg_str = json.dumps(self.hsg_dict)
        self.equipment_dict['addenda': self.addenda]
        self.equipment_dict['subtrahenda': self.subtrahenda]
        equipment_str = json.dumps(self.equipment_dict, sort_keys=True)
        
        my_header = self.description + '\n' + hsg_str + '\n' + equipment_str
        
        np.savetxt(os.path.join(folder_str, self.file_name), self.raw_array, 
                   delimiter=',', header=my_header, comments='#', fmt='%d')


class PL_image(EMCCD_image):
    '''
    This class is for handling PL images and turning them into simple spectra.
    '''
    
    def __init__(self, raw_array, file_name, description, pl_dict, equipment_dict):
        '''
        This initializes a PL image instance.  I expect the header to be slightly
        different from the HSG or absorption headers.
        
        image_array = 400x1600 array with data in it
        bg_array = appropriate bg_array
        pl_dict = the important parameters for hsg: 
            sample_name
            sample_temperature
            excitation_power
            excitation_lambda
        experiment_dict = the important experimental apparatus conditions:
            CCD_temperature
            exposure
            gain
            y_min
            y_max
            grating
            center_lambda
            slits
            dark_region (maybe not that useful if can look at y_max + n)
        '''
        self.raw_array = np.array(raw_array)
        self.file_name = file_name
        self.description = description
        self.pl_dict = pl_dict
        self.equipment_dict = equipment_dict
        self.clean_array = None
        self.spectrum = None
        self.addenda = [0, file_name] # This is important for keeping track of addition and subtraction
        self.subtrahenda = []
    
    def save_spectrum(self, folder_str='PL files'):
        '''
        Saves the general spectrum.  Unsure if we need it, but, again, seems
        useful for novel, basic stuff.
        '''
        try:
            os.mkdir(folder_str)
        except OSError, e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise
        
        pl_str = json.dumps(self.pl_dict)
        self.equipment_dict['addenda': self.addenda]
        self.equipment_dict['subtrahenda': self.subtrahenda]
        equipment_str = json.dumps(self.equipment_dict, sort_keys=True)
        
        save_file_name = 'pl_' + self.file_name
        origin_import = '\nWavelength,Signal\nnm,arb. u.'
        my_header = self.description + '\n' + pl_str + '\n' + equipment_str + origin_import
        np.savetxt(os.path.join(folder_str, save_file_name), self.spectrum, 
                   delimiter=',', header=my_header, comments='#', fmt='%f')

    def save_images(self, folder_str='Raw files'):
        '''
        Saves the raw_array, not the cleaned one.  Cleaning isn't that hard, 
        and how we do it could change in the future.
        
        This really depends on how the folders are initialized by the UI.  Will
        they already exist by the time we get to saving images, or do they need
        to be created on the fly?
        
        Also, I'm pretty sure self.raw_array is still ints?
        '''
        try:
            os.mkdir(folder_str)
        except OSError, e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise
        
        pl_str = json.dumps(self.pl_dict)
        self.equipment_dict['addenda': self.addenda]
        self.equipment_dict['subtrahenda': self.subtrahenda]
        equipment_str = json.dumps(self.equipment_dict, sort_keys=True)
        
        my_header = self.description + '\n' + pl_str + '\n' + equipment_str
        
        np.savetxt(os.path.join(folder_str, self.file_name), self.raw_array, 
                   delimiter=',', header=my_header, comments='#', fmt='%d')
    
class Abs_image(EMCCD_image):
    '''
    This class is for handling absorbance images to be able to spit out just
    the relevant 2x1600 spectrum.  It should be able to load both the blank
    spectrum and the sample spectrum, then divide them to give the absorbance.
    '''
    
    def __init__(self, trans_array, blank_array, file_name, blank_file_name, description, abs_dict, equipment_dict):
        '''
        This will initialize an absorbance image instance.  The header will
        be slightly different from the others, but this should also load
        and clean the blank spectrum.
        
        raw_array = image of transmitted light through sample
        blank_array = the LED reference array to calculate absorbance from
        bg_array = appropriate bg_array
        hsg_dict = the important parameters for hsg: 
            sample_name
            sample_temperature
            led_center
        experiment_dict = the important experimental apparatus conditions:
            CCD_temperature
            exposure
            gain
            y_min
            y_max
            grating
            center_lambda
            slits
            dark_region (maybe not that useful if can look at y_max + n)
        '''
        self.trans_array = np.array(trans_array)
        self.blank_array = np.array(blank_array)
        self.file_name = file_name
        self.blank_file_name = blank_file_name
        self.description = description
        self.abs_dict = abs_dict
        self.equipment_dict = equipment_dict
        self.clean_array = None
        self.spectrum = None
        self.addenda = [0, file_name] # This is important for keeping track of addition and subtraction
        self.subtrahenda = []
    
    def __div__(self, other):
        '''
        This implementation of division is specialized to the absorbance 
        measurement.
        '''
        if self.spectrum is None or other.spectrum is None:
            raise Exception('The first array has not been cleaned yet')
        #ret = copy.deepcopy(self)
        
        if type(other) in (int, float):
            pass
        else:
            pass
        
    def cosmic_ray_removal(self, mygain=2.2, myreadnoise=3.0, mysigclip=5.0, mysigfrac=0.5, myobjlim=5.0, myverbose=True):
        '''
        This is a single operation of cosmic ray removal.

        If EMCCD isn't cold enough, the hot pixels wil be removed as well.  I 
        don't know if this is a bad thing?  I think it should just be a thing
        that doesn't happen.
        
        mygain = the gain.  This does not seem to actually be the EM gain of 
                 the EMCCD
        myreadnoise = Level (imprecise!) of read noise used in the statistical
                      model built to recognize cosmic arrays.  It's a function
                      of gain on our CCD, I believe.  Dark current should be 
                      separate, technically, but it would look like noise 
                      because of shot noise and crap
        mysigclip = I forget
        mysicfrac = I forget
        myobjlim = I forget
        myverbose = Tells hsg_cosmics to print out what it's doing
        
        creates clean arrays of raw and blank
        '''
        image_removal = cosmics.cosmicsimage(self.trans_array, gain=mygain, # I don't understand gain
                                             readnoise=myreadnoise, 
                                             sigclip=mysigclip, 
                                             sigfrac=mysigfrac, 
                                             objlim=myobjlim)
        image_removal.run(maxiter=4)
        
        blank_removal = cosmics.cosmicsimage(self.blank_array, gain=mygain, # I don't understand gain
                                             readnoise=myreadnoise, 
                                             sigclip=mysigclip, 
                                             sigfrac=mysigfrac, 
                                             objlim=myobjlim)
        blank_removal.run(maxiter=4)
        
        self.clean_array = image_removal.cleanarray
        self.clean_blank = blank_removal.cleanarray
    
    def make_spectrum(self):
        '''
        I can't decide what is easier, doing the absorbance calculation 
        internally, or doing it with division.  I am currently leaning towards
        internaly.
        '''
        self.blank_spec = self.clean_blank[:,self.equipment_dict['y_min']:self.equipment_dict['y_max']].sum(axis=1)       
        self.trans_spec = self.clean_array[:,self.equipment_dict['y_min']:self.equipment_dict['y_max']].sum(axis=1)
        self.abs_spec = np.log10(self.blank_spec / self.trans_spec)
        
        wavelengths = gen_wavelengths(self.equipment_dict['center_lambda'], 
                                      self.equipment_dict['grating'])
        self.spectrum = np.concatenate((wavelengths, self.blank_spec, 
                                        self.trans_spec, self.abs_spec)).reshape(4,1600).T
        
    def save_spectrum(self, folder_str="Absorbance files"):
        '''
        Saves the appropriate data.
        '''
        try:
            os.mkdir(folder_str)
        except OSError, e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise
        
        abs_str = json.dumps(self.abs_dict)
        self.equipment_dict['addenda': self.addenda]
        self.equipment_dict['subtrahenda': self.subtrahenda]
        equipment_str = json.dumps(self.equipment_dict, sort_keys=True)
        
        save_file_name = 'abs_' + self.file_name
        origin_import = '\nWavelength,Blank,Transmitted,Absorbance\nnm,arb. u.,arb. u.,log10'
        my_header = self.description + '\n' + abs_str + '\n' + equipment_str + origin_import
        np.savetxt(os.path.join(folder_str, save_file_name), self.spectrum, 
                   delimiter=',', header=my_header, comments='#', fmt='%f')

    def save_images(self, folder_str='Raw files'):
        '''
        Saves the raw_array and blank_array, not the cleaned ones.  Cleaning 
        isn't that hard, and how we do it could change in the future.
        
        This really depends on how the folders are initialized by the UI.  Will
        they already exist by the time we get to saving images, or do they need
        to be created on the fly?
        
        Also, I'm pretty sure self.raw_array is still ints?
        '''
        try:
            os.mkdir(folder_str)
        except OSError, e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise
        
        abs_str = json.dumps(self.abs_dict)
        self.equipment_dict['addenda': self.addenda]
        self.equipment_dict['subtrahenda': self.subtrahenda]
        equipment_str = json.dumps(self.equipment_dict, sort_keys=True)
        filename = self.file_name + '.txt'
        
        my_header = self.description + '\n' + abs_str + '\n' + equipment_str
        
        np.savetxt(os.path.join(folder_str, filename), self.trans_array, 
                   delimiter=',', header=my_header, comments='#', fmt='%f')
        np.savetxt(os.path.join(folder_str, self.blank_file_name), 
                   self.blank_array, delimiter=',', header=my_header, 
                   comments='#', fmt='%d')
        
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