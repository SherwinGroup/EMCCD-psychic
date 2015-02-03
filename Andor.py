# -*- coding: utf-8 -*-
"""
Created on Mon Feb 02 10:17:34 2015

@author: dvalovcin
"""

import numpy as np
from ctypes import *



class AndorEMCCD(object):
    
    def __init__(self):
        self.registerFunctions()
        
#        self.data = c_long * self.height*self.width
        
    def registerFunctions(self):
        ''' This function serves to import all of the functions
        from the DLL, define them as the class's own for neatness, and
        set up prototypes.
        
        All functions follow the convention self.dllFunctionName so that it
        is easier to see which are coming directly from the dll.'''
        try:
            dll = CDLL('atmcd64d') #Change this to the appropriate name
        except:
            print 'Error loading the DLL. Is it in the path?'
            return
        
        '''
        CoolerON: Switches ON the cooling. The rate of temperature change is 
        controlled until the temperature is within 3deg of the set value. 
        Control is returned immediately to the calling application.
        
        Parameters
        ----------
        None
        
        Return
        ------
        unsigned int
            DRV_SUCCESS         Temperature controller switched ON.
            DRV_NOT_INITIALIZED System not initialized.
            DRV_ACQUIRING       Acquisition in progress.
            DRV_ERROR_ACK       Unable to communicate with card.
        '''
        self.dllCoolerON = dll.CoolerON
        self.dllCoolerON.restype = c_uint
        self.dllCoolerON.argtypes = []
        
        '''
        CoolerOFF: Switches OFF the cooling. The rate of temperature change is 
        controlled until the temperature reaches 0º. Control is returned 
        immediately to the calling application.
        
        Parameters
        ----------
        None
        
        Return
        ------
        unsigned int
            DRV_SUCCESS         Temperature controller switched ON.
            DRV_NOT_INITIALIZED System not initialized.
            DRV_ACQUIRING       Acquisition in progress.
            DRV_ERROR_ACK       Unable to communicate with card.
        '''
        self.dllCoolerOFF = dll.CoolerOFF
        self.dllCoolerOFF.restype = c_uint
        self.dllCoolerOFF.argtypes = []
        
        '''
        GetAcquiredData: This function will return the data from the last 
        acquisition. The data are returned as long integers (32-bit signed 
        integers). The “array” must be large enough to hold the complete data set.
        
        Parameters
        ----------
        long* array: pointer to data storage allocated by the user.
        long size: total number of pixels.
        
        Return
        ------
        unsigned int
            DRV_SUCCESS         Temperature controller switched ON.
            DRV_NOT_INITIALIZED System not initialized.
            DRV_ACQUIRING       Acquisition in progress.
            DRV_ERROR_ACK       Unable to communicate with card.
            DRV_P1INVALID       Invalid pointer (i.e. NULL).
            DRV_P2INVALID       Array size is too small.
        '''
        self.dllGetAcquiredData = dll.GetAcquiredData
        self.dllGetAcquiredData.resType = c_uint
        self.dllGetAcquiredData.argtypes = [POINTER(c_long), c_long]
        
        '''
        GetDetector: This function returns the size of the detector in 
        pixels. The horizontal axis is taken to be the axis parallel to the
        readout register.
        
        Parameters
        ----------
        int* xpixels: number of horizontal pixels.
        int* ypixels: number of vertical pixels.
        
        Return
        ------
        unsigned int
            DRV_SUCCESS         Temperature controller switched ON.
            DRV_NOT_INITIALIZED System not initialized.
            DRV_ACQUIRING       Acquisition in progress.
        '''
        self.dllGetDetector = dll.GetDetector
        self.dllGetDetector.resType = c_uint
        self.dllGetDetector.argtypes = [POINTER(c_int), POINTER(c_int)]
        
        '''
        GetMostRecentImage: This function will update the data array with the 
        most recently acquired image in any acquisition mode. The data are
        returned as long integers (32-bit signed integers). The "array" must 
        be exactly the same size as the complete image.
        
        Parameters
        ----------
        long* array: pointer to data storage allocated by the user.
        unsigned long size: total number of pixels.
        
        Return
        ------
        unsigned int
            DRV_SUCCESS         Temperature controller switched ON.
            DRV_NOT_INITIALIZED System not initialized.
            DRV_ERROR_ACK       Unable to communicate with card.
            DRV_P1INVALID       Invalid pointer (i.e. NULL).
            DRV_P2INVALID       Array size is too small.
            DRV_NO_NEW_DATA     There is no new data yet.
        '''
        self.dllGetMostRecentImage = dll.GetMostRecentImage
        self.dllGetMostRecentImage.restype = c_uint
        self.dllGetMostRecentImage.argtypes = [POINTER(c_long), c_ulong]
            
        '''
        GetStatus: This function will update the data array with the 
        most recently acquired image in any acquisition mode. The data are
        returned as long integers (32-bit signed integers). The "array" must 
        be exactly the same size as the complete image.
        
        Parameters
        ----------
        int* status: current status
            DRV_IDLE                    IDLE waiting on instructions.
            DRV_TEMPCYCLE               Executing temperature cycle.
            DRV_ACQUIRING               Acquisition in progress.
            DRV_ACCUM_TIME_NOT_MET      Unable to meet Accumulate cycle time.
            DRV_KINETIC_TIME_NOT_MET    Unable to meet Kinetic cycle time.
            DRV_ERROR_ACK               Unable to communicate with card.
            DRV_ACQ_BUFFER              Computer unable to read the data via the
                                            ISA slotat the required rate.
            DRV_SPOOLERROR              Overflow of the spool buffer.

        Return
        ------
        unsigned int
            DRV_SUCCESS         Temperature controller switched ON.
            DRV_NOT_INITIALIZED System not initialized.
        '''
        self.dllGetStatus = dll.GetStatus
        self.dllGetStatus.restype = c_uint
        self.dllGetStatus.argtypes = [POINTER(c_int)]
        
        '''
        GetTemperature: This function returns the temperature of the detector to 
        the nearest degree. It also gives the status of cooling process.
        
        Parameters
        ----------
        int* temperature: temperature of the detector
        
        Return
        ------
        unsigned int
            DRV_NOT_INITIALIZED     System not initialized.
            DRV_ACQUIRING           Acquisition in progress.
            DRV_ERROR_ACK           Unable to communicate with card.
            DRV_TEMP_OFF            Temperature is OFF.
            DRV_TEMP_STABILIZED     Temperature has stabilized at set point.
            DRV_TEMP_NOT_REACHED    Temperature has not reached set point.
        '''
        self.dllGetTemperature = dll.GetTemperature
        self.dllGetTemperature.restype = c_uint
        self.dllGetTemperature.argtypes = [POINTER(c_int)]
        
        '''
        Initialize: This function will initialize the Andor Solis System. As 
        part of the initialization procedure on some cameras (i.e. Classic, 
        Istar and earlier iXion) the DLL will need access the following file:
            DETECTOR.INI which contains information relating to the detector
            head, number pixels, readout speeds etc.
        
        Parameters
        ----------
        char* directory: Path to the directory containing the files
        
        Return
        ------
        unsigned int
            DRV_SUCCESS             System fully initialized.
            DRV_VXDNOTINSTALLED     VxD not loaded
            DRV_INIERROR            Unable to load “DETECTOR.INI”.
            DRV_COFERROR            Unable to load “*.COF”.
            DRV_FLEXERROR           Unable to load “*.RBF”.
            DRV_ERROR_ACK           Unable to communicate with card.
            DRV_ERROR_FILELOAD      Unable to load “*.COF” or “*.RBF” files.
            DRV_ERROR_PAGELOCK      Unable to acquire lock on requested memory.
            DRV_USBERROR            Unable to detect USB device or not USB2.0.
        '''
        self.dllInitialize = dll.Initialize
        self.dllInitialize.restype = c_uint
        self.dllInitialize.argtypes = [c_char_p]
        
        '''
        PrepareAcquisition: This function reads the current acquisition setup 
        and allocates and clears any memory that will be used during the
        acquisition. The function call is not required as it will be called
        automatically by the StartAcquisition function if it has not already
        been called externally. However for long kinetic series acquisitions 
        the time to allocate and clear any memory can be quite long which can
        result in a long delay between calling StartAcquisition and the acquisition
        actually commencing. For iDus, there is an additional delay caused by the
        camera being set-up with any new acquisition parameters. Calling 
        PrepareAcquisition first will reduce this delay in the StartAcquisition call.
        
        Parameters
        ----------
        NONE
        
        Return
        ------
        unsigned int
            DRV_SUCCESS             Acquisition prepared.
            DRV_NOT_INITIALIZED     System not initialized.
            DRV_ACQUIRING           Acquisition in progress.
            DRV_VXDNOTINSTALLED     VxD not loaded
            DRV_ERROR_ACK           Unable to communicate with card.
            DRV_INIERROR            Unable to load “DETECTOR.INI”.
            DRV_ACQERROR            Acquisition Setting Invalid 
            DRV_ERROR_PAGELOCK      Unable to acquire lock on requested memory.
            DRV_INVALID_FILTER      Filter not available for current acquisition
            DRV_IOCERROR            Integrate On Chip setup error
        '''
        self.dllPrepareAcquisition = dll.PrepareAcquisition
        self.dllPrepareAcquisition
        
        
        
        
        
        
        
        
    def parseReturn(self, value):
        '''Pass in the return value of a function and this will return 
        the string which it represents'''
        values = {
            20001: 'DRV_ERROR_CODES',
            20002: 'DRV_SUCCESS',
            20003: 'DRV_VXDNOTINSTALLED',
            20004: 'DRV_ERROR_SCAN',
            20005: 'DRV_ERROR_CHECK_SUM',
            20006: 'DRV_ERROR_FILELOAD',
            20007: 'DRV_UNKNOWN_FUNCTION',
            20008: 'DRV_ERROR_VXD_INIT',
            20009: 'DRV_ERROR_ADDRESS',
            20010: 'DRV_ERROR_PAGELOCK',
            20011: 'DRV_ERROR_PAGE_UNLOCK',
            20012: 'DRV_ERROR_BOARDTEST',
            20013: 'DRV_ERROR_ACK',
            20014: 'DRV_ERROR_UP_FIFO',
            20015: 'DRV_ERROR_PATTERN',
            20017: 'DRV_ACQUISITION_ERRORS',
            20018: 'DRV_ACQ_BUFFER',
            20019: 'DRV_ACQ_DOWNFIFO_FULL',
            20020: 'DRV_PROC_UNKNOWN_INSTRUCTION',
            20021: 'DRV_ILLEGAL_OP_CODE',
            20022: 'DRV_KINETIC_TIME_NOT_MET',
            20023: 'DRV_ACCUM_TIME_NOT_MET',
            20024: 'DRV_NO_NEW_DATA',
            20026: 'DRV_SPOOLERROR',
            20033: 'DRV_TEMPERATURE_CODES',
            20034: 'DRV_TEMPERATURE_OFF',
            20035: 'DRV_TEMPERATURE_NOT_STABILIZED',
            20036: 'DRV_TEMPERATURE_STABILIZED',
            20037: 'DRV_TEMPERATURE_NOT_REACHED',
            20038: 'DRV_TEMPERATURE_OUT_RANGE',
            20039: 'DRV_TEMPERATURE_NOT_SUPPORTED',
            20040: 'DRV_TEMPERATURE_DRIFT',
            20049: 'DRV_GENERAL_ERRORS',
            20050: 'DRV_INVALID_AUX',
            20051: 'DRV_COF_NOTLOADED',
            20052: 'DRV_FPGAPROG',
            20053: 'DRV_FLEXERROR',
            20054: 'DRV_GPIBERROR',
            20064: 'DRV_DATATYPE',
            20065: 'DRV_DRIVER_ERRORS',
            20066: 'DRV_P1INVALID',
            20067: 'DRV_P2INVALID',
            20068: 'DRV_P3INVALID',
            20069: 'DRV_P4INVALID',
            20070: 'DRV_INIERROR',
            20071: 'DRV_COFERROR',
            20072: 'DRV_ACQUIRING',
            20073: 'DRV_IDLE',
            20074: 'DRV_TEMPCYCLE',
            20075: 'DRV_NOT_INITIALIZED',
            20076: 'DRV_P5INVALID',
            20077: 'DRV_P6INVALID',
            20078: 'DRV_INVALID_MODE',
            20079: 'DRV_INVALID_FILTER',
            20080: 'DRV_I2CERRORS',
            20081: 'DRV_DRV_I2CDEVNOTFOUND',
            20082: 'DRV_I2CTIMEOUT',
            20083: 'DRV_P7INVALID',
            20089: 'DRV_USBERROR',
            20090: 'DRV_IOCERROR',
            20091: 'DRV_NOT_SUPPORTED'}
        ret = values.get(value, 'NotRegistered')
        return ret 
            
            
            








a = AndorEMCCD()









































