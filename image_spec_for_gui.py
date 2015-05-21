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

import logging
log = logging.getLogger("EMCCD")

class EMCCD_image(object):
    origin_import = '\nWavelength,Signal\nnm,arb. u.'
    
    def __init__(self, raw_array, file_name, file_no, description, equipment_dict):
        """
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
        """
        self.raw_array = np.array(raw_array)
        self.raw_shape = self.raw_array.shape
        self.file_name = file_name
        self.file_no = file_no
        self.description = description
        self.equipment_dict = equipment_dict
        if self.equipment_dict['y_max'] - self.equipment_dict['y_min'] > int(self.raw_shape[0]):
            log.warning("y_min and y_max were set incorrectly")
            self.equipment_dict['y_max'] = int(self.raw_shape[0]) - 1
            self.equipment_dict['y_min'] = 0
        self.clean_array = None
        self.spectrum = None
        self.addenda = [0, file_name + str(file_no)] # This is important for keeping track of addition and subtraction
        self.subtrahenda = []
        self.equipment_dict["background_darkcount_std"] = -1

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
            log.error("Unable to add: First array not cleaned")
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
                print "self:{}, ret:{}, other:{}".format(
                    self.equipment_dict['center_lambda'],
                    ret.equipment_dict['center_lambda'],
                    other.equipment_dict['center_lambda']
                )
                # raise Exception('Source: EMCCD_image.__add__\nThese are not from the same grating settings')
                log.error("Unable to add, data not from same grating settings")
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
    
    def cosmic_ray_removal(self, mygain=10, myreadnoise=0.2, mysigclip=5.0, mysigfrac=0.01, myobjlim=3.0, myverbose=True):
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
        # print "Base line is ", self.dark_mean
        # print "Standard deviation is ", self.std_dev
        height = self.equipment_dict['y_max'] - self.equipment_dict['y_min']
        self.spectrum[:,1] = self.spectrum[:, 1] - self.dark_mean*height
        self.addenda[0] += self.dark_mean*height
        self.clean_array -= self.dark_mean
    
    def save_spectrum(self, folder_str='Spectrum files', prefix=None):
        '''
        Saves the general spectrum.  Unsure if we need it, but, again, seems
        useful for novel, basic stuff.
        '''

        self.equipment_dict['addenda'] = self.addenda
        self.equipment_dict['subtrahenda'] = self.subtrahenda
        equipment_str = json.dumps(self.equipment_dict, sort_keys=True)
        origin_import = self.origin_import

        filename = self.getFileName(prefix)


        filename += "_spectrum.txt"
        my_header = '#' + equipment_str + '\n' + '#' + self.description.replace('\n','\n#') + origin_import
        np.savetxt(os.path.join(folder_str, 'Spectra', self.file_name, filename), self.spectrum,
                   delimiter=',', header=my_header, comments = '', fmt='%f')

        # print "Save image.\nDirectory: {}".format(
        #     os.path.join(folder_str, 'Spectra', self.file_name, filename)
        # )

    def getFileName(self, prefix=None):
        """
        Convenience function to get the name used for saving.
        """
        # All the data will end up doig the same thing,
        # only difference is the preffix to the name (?)
        # which can also be set specifically with the function call
        if prefix is None:
            # Get the name of the class calling it
            name = type(self).__name__.lower()
            if "hsg" in name:
                filename = "hsg_"
            elif "pl" in name:
                filename = "pl_"
            elif "abs" in name:
                filename = "absRaw_"
            else:
                filename = ""
        else:
            filename = str(prefix)


        filename += self.file_name + self.file_no
        return filename
    
    def save_images(self, folder_str='Raw files', prefix=None):
        '''
        Saves the raw_array, not the cleaned one.  Cleaning isn't that hard, 
        and how we do it could change in the future.
        
        This really depends on how the folders are initialized by the UI.  Will
        they already exist by the time we get to saving images, or do they need
        to be created on the fly?
        
        Also, I'm pretty sure self.raw_array is still ints?
        '''
        self.equipment_dict['addenda'] = self.addenda
        self.equipment_dict['subtrahenda'] = self.subtrahenda
        try:
            equipment_str = json.dumps(self.equipment_dict, sort_keys=True)
        except:
            print "Source: EMCCD_image.save_images\nJSON FAILED"
            print self.equipment_dict
            return
        
        my_header = "#" + equipment_str + '\n#' +  self.description.replace('\n','\n#')



        # All the data will end up doig the same thing,
        # only difference is the preffix to the name (?)
        # which can also be set specifically with the function call
        if prefix is None:
            name = type(self).__name__.lower()
            if "hsg" in name:
                filename = "hsg_"
                print "hsg"
            elif "pl" in name:
                filename = "pl_"
                print "pl"
            elif "abs" in name:
                filename = "absRaw_"
            else:
                filename = ""
        else:
            filename = str(prefix)

        filename += self.file_name + self.file_no + '.txt'
        np.savetxt(os.path.join(folder_str, "Images", filename), self.raw_array,
               delimiter=',', header=my_header, comments = '#', fmt='%d')
        print "Saved image\nDirectory: {}".format(
            os.path.join(folder_str, "Images", filename)
        )


class HSG_image(EMCCD_image):
    '''
    This subclass will specialize in HSG initializing and saving, which mostly
    has to do with what the header in the file is at this point.  
    '''
    
    def __init__(self, raw_array, file_name, file_no, description, equipment_dict):
        """
        Currently unchanged from the base class.
        """
        super(HSG_image, self).__init__(raw_array, file_name, file_no, description, equipment_dict)

    def __add__(self, other):
        """
        Want to also add field information from the FEL
        """
        ret = super(HSG_image, self).__add__(other)
        # ret.equipment_dict["fieldStrength"].extend(other.equipment_dict["fieldStrength"])
        # ret.equipment_dict["fieldInt"].extend(other.equipment_dict["fieldInt"])
        # ret.equipment_dict["fel_pulses"] += other.equipment_dict["fel_pulses"]

        return ret


    def __sub__(self, other):
        """
        Want to also add field information from the FEL
        """
        ret = super(HSG_image, self).__sub__(other)
        # ret.equipment_dict["fieldStrength"].extend(other.equipment_dict["fieldStrength"])
        # ret.equipment_dict["fieldInt"].extend(other.equipment_dict["fieldInt"])
        # ret.equipment_dict["fel_pulses"] += other.equipment_dict["fel_pulses"]

        return ret



    def save_spectrum(self, folder_str='HSG files'):
        '''
        Saves the general spectrum.  Unsure if we need it, but, again, seems
        useful for novel, basic stuff.
        '''
        super(HSG_image, self).save_spectrum(folder_str=folder_str)

        return


    def save_images(self, folder_str='Raw files'):
        '''
        Saves the raw_array, not the cleaned one.  Cleaning isn't that hard, 
        and how we do it could change in the future.
        
        This really depends on how the folders are initialized by the UI.  Will
        they already exist by the time we get to saving images, or do they need
        to be created on the fly?
        
        Also, I'm pretty sure self.raw_array is still ints?
        '''

        super(HSG_image, self).save_images(folder_str=folder_str)
        return


class PL_image(EMCCD_image):
    '''
    This class is for handling PL images and turning them into simple spectra.
    '''
    
    # def __init__(self, raw_array, file_name, description, pl_dict, equipment_dict):
    #     '''
    #     This initializes a PL image instance.  I expect the header to be slightly
    #     different from the HSG or absorption headers.
    #
    #     image_array = 400x1600 array with data in it
    #     bg_array = appropriate bg_array
    #     pl_dict = the important parameters for hsg:
    #         sample_name
    #         sample_temperature
    #         excitation_power
    #         excitation_lambda
    #     experiment_dict = the important experimental apparatus conditions:
    #         CCD_temperature
    #         exposure
    #         gain
    #         y_min
    #         y_max
    #         grating
    #         center_lambda
    #         slits
    #         dark_region (maybe not that useful if can look at y_max + n)
    #     '''
    #     self.raw_array = np.array(raw_array)
    #     self.file_name = file_name
    #     self.description = description
    #     self.pl_dict = pl_dict
    #     self.equipment_dict = equipment_dict
    #     self.clean_array = None
    #     self.spectrum = None
    #     self.addenda = [0, file_name] # This is important for keeping track of addition and subtraction
    #     self.subtrahenda = []
    
    # def save_spectrum(self, folder_str='PL files'):
    #     '''
    #     Saves the general spectrum.  Unsure if we need it, but, again, seems
    #     useful for novel, basic stuff.
    #     '''
    #     try:
    #         os.mkdir(folder_str)
    #     except OSError, e:
    #         if e.errno == errno.EEXIST:
    #             pass
    #         else:
    #             raise
    #
    #     pl_str = json.dumps(self.pl_dict)
    #     self.equipment_dict['addenda': self.addenda]
    #     self.equipment_dict['subtrahenda': self.subtrahenda]
    #     equipment_str = json.dumps(self.equipment_dict, sort_keys=True)
    #
    #     save_file_name = 'pl_' + self.file_name
    #     origin_import = '\nWavelength,Signal\nnm,arb. u.'
    #     my_header = self.description + '\n' + pl_str + '\n' + equipment_str + origin_import
    #     np.savetxt(os.path.join(folder_str, save_file_name), self.spectrum,
    #                delimiter=',', header=my_header, comments='#', fmt='%f')
    #
    # def save_images(self, folder_str='Raw files'):
    #     '''
    #     Saves the raw_array, not the cleaned one.  Cleaning isn't that hard,
    #     and how we do it could change in the future.
    #
    #     This really depends on how the folders are initialized by the UI.  Will
    #     they already exist by the time we get to saving images, or do they need
    #     to be created on the fly?
    #
    #     Also, I'm pretty sure self.raw_array is still ints?
    #     '''
    #     try:
    #         os.mkdir(folder_str)
    #     except OSError, e:
    #         if e.errno == errno.EEXIST:
    #             pass
    #         else:
    #             raise
    #
    #     pl_str = json.dumps(self.pl_dict)
    #     self.equipment_dict['addenda': self.addenda]
    #     self.equipment_dict['subtrahenda': self.subtrahenda]
    #     equipment_str = json.dumps(self.equipment_dict, sort_keys=True)
    #
    #     my_header = self.description + '\n' + pl_str + '\n' + equipment_str
    #
    #     np.savetxt(os.path.join(folder_str, self.file_name), self.raw_array,
    #                delimiter=',', header=my_header, comments='#', fmt='%d')

    
class Abs_image(EMCCD_image):
    origin_import = '\nWavelength,Raw Trans\nnm,arb. u.'
    def __init__(self, raw_array, file_name, file_no, description, equipment_dict):
        super(Abs_image, self).__init__(raw_array, file_name, file_no, description, equipment_dict)
        self.abs_spec = None
        self.equipment_dict["reference_file"] = ""
    def __eq__(self, other):
        if type(other) is not type(self):
            print "not same type: {}/{}/{}".format(type(other), type(self), type(Abs_image()))
            return False
        if self.equipment_dict["gain"] != other.equipment_dict["gain"]:
            return False
        if self.equipment_dict["exposure"] != other.equipment_dict["exposure"]:
            return False
        if self.equipment_dict["grating"] != other.equipment_dict["grating"]:
            return False
        if self.equipment_dict["center_lambda"] != other.equipment_dict["center_lambda"]:
            return False
        return True

    def __div__(self, other):
        # self is the reference spectrum
        # other is the tranmission data

        if type(other) is not type(self):
            raise TypeError("Cannot divide {}".format(type(other)))
        ret = copy.deepcopy(other)
        abs_spec = np.log10(self.spectrum[:,1] / other.spectrum[:,1])
        wavelengths = gen_wavelengths(self.equipment_dict['center_lambda'],
                                      self.equipment_dict['grating'])

        # First is blank
        # other is transmission
        ret.spectrum = np.concatenate((wavelengths, self.spectrum[:,1].T,
                                        other.spectrum[:,1].T, abs_spec)).reshape(4,1600).T
        return ret





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


def calc_THz_intensity(total_energy, window_trans=1, sample_eff_field=1, pulse_width=37,
                       ratio=None, radius=0.05, ito_reflect=0.7):
    """
    This will calculate the THz intensity at the sample during the cavity dump.
    Do not enter a ratio if you want to do an average intensity calculation.

    total_energy - the total energy in the FEL pulse, in mJ
    pulse_width - the FWHM of the pulse as measured by the fast pyro, in ns
                  if you want for cavity dump intensity, use FWHM of the front
                  porch. Assumed to be 37 ns (pulse width for cavity dump
                  based on photon travel time for two round trips in undulator)
    window_trans - the power transmission of the cryostat window
    sample_eff_field - the effective _field_ at the front of the sample
    ratio - the ratio of the cavity dump to the front porch
    radius - the radius of the FEL spot, assumed to be 0.05 cm
    ito_reflect - the power reflection of the ITO beam combiner, assumed to be
                  around 0.7

    return - the intensity in the FEL spot in W/cm^2
    """
    area = np.pi * (radius)**2
    if ratio is not None:
        # power = 1e-3 * total_energy / (37e-9 + (pulse_width * 1e-9) / ratio)
        power = 1e-3 * total_energy * ratio/ (pulse_width * 1e-9)
    else:
        power = 1e-3 * total_energy / (pulse_width * 1e-9)
    return ito_reflect * window_trans * sample_eff_field**2 * power / area

def calc_THz_field(intensity, n=3.59):
    """
    This will calculate the THz field strength in the sample

    intensity - the intensity of the THz field
    n - the index of the material at the THz frequency, assumed to be 3.59 for GaAs

    return - the peak electric field in V/cm
    """
    return (2 * intensity / (8.85e-12 * 2.99e8 * n))**0.5