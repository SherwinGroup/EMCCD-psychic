# -*- coding: utf-8 -*-
"""
Created on Sat Feb 14 19:00:33 2015

@author: Home
"""

import numpy as np
import time



class myCallable(object):
    ''' Need a class which is callable, but also
        need it to have the argtypes and restype 
        parameters to match the calls made setting up the CCD. '''
    def __init__(self, func=None, st = ''):
        self.argtypes = []
        self.restype = None
        self.st = st
        self.func = func
        
    def __call__(self, *args):
        print ' '*10+self.st, args
        self.func(args)
        return 20002

class fAndorEMCCD(object):
    def __init__(self):
        self.CoolerON = myCallable(self.__voidReturn, 'CoolerON')
        self.CoolerOFF = myCallable(self.__voidReturn, 'CoolerOFF')
        self.CancelWait = myCallable(self.__voidReturn, 'CancelWait')
        self.GetAcquiredData = myCallable(self.__getData, 'GetAcquiredData')
        self.GetDetector = myCallable(self.__getDet, 'GetDetector')
        self.GetHSSpeed = myCallable(self.__getHSS, 'GetHSSpeed')
        self.GetMostRecentImage = myCallable(self.__voidReturn, 'GetMostRecentImage')
        self.GetNumberADChannels = myCallable(self.__getNum, 'GetNumberADChannels')
        self.GetNumberHSSpeeds = myCallable(self.__getNum, 'GetNumberHSSpeeds')
        self.GetNumberVSSpeeds = myCallable(self.__getNum, 'GetNumberVSSpeeds')
        self.GetStatus = myCallable(self.__getNum, 'GetStatus')
        self.GetTemperature = myCallable(self.__getNum, 'GetTemperature')
        self.GetVSSpeed = myCallable(self.__getHSS, 'GetVSSpeed')
        self.Initialize = myCallable(self.__voidReturn, 'Initialize')
        self.PrepareAcquisition = myCallable(self.__voidReturn, 'PrepAcq')
        self.SetAcquisitionMode = myCallable(self.__voidReturn, 'SetAcqMode')
        self.SetADChannel = myCallable(self.__voidReturn, 'SetADChannel')
        self.SetEMCCDGain = myCallable(self.__voidReturn, 'SetEMCCDGain')
        self.SetExposureTime = myCallable(self.__voidReturn, 'SetExposureTime')
        self.SetGain = myCallable(self.__voidReturn, 'SetGain')
        self.SetHSSpeed = myCallable(self.__voidReturn, 'SetHSSpeed')
        self.SetImage = myCallable(self.__voidReturn, 'SetImage')
        self.SetReadMode = myCallable(self.__voidReturn, 'SetReadout')
        self.SetShutter = myCallable(self.__voidReturn, 'SetShutter')
        self.SetShutterEx = myCallable(self.__voidReturn, 'SetShutterEx')
        self.SetTemperature = myCallable(self.__voidReturn, 'SetTemp')
        self.SetTriggerMode = myCallable(self.__voidReturn, 'SetTriggerMode')
        self.SetVSSpeed = myCallable(self.__voidReturn, 'SetVSSpeed')
        self.ShutDown = myCallable(self.__voidReturn, "SHUT 'ER DOWN")
        self.StartAcquisition = myCallable(self.__voidReturn, 'Start Acquisition')
        self.WaitForAcquisition = myCallable(self.__wait, 'WaitForAcuisition')

        
    def __voidReturn(self, *args):
        pass
    

    def __getData(self, *args):
        arr = args[0][0]
        for i in range(args[0][1]):
            arr[i] = np.random.random_integers(6000)
            
    def __getDet(self, *args):
        x = args[0][0]
        y = args[0][1]
        x.value = 1600
        y.value = 400
        
    def __getHSS(self, *args):
        x = args[0][-1]
        x.value = np.random.randint(100)
    
    def __getNum(self, *args):
        x = args[0][-1]
        x.value = np.random.randint(1, 5)

    def __wait(self, *args):
        # Wait a random amount of time to simulate it
        time.sleep(np.random.randint(10, 30))
    
    

    
        



# a = fAndorEMCCD()


















































