# -*- coding: utf-8 -*-
"""
Created on Sat Feb 14 19:00:33 2015

@author: Home
"""

import numpy as np
import time
import logging
log = logging.getLogger("Andor")



class myCallable(object):
    ''' Need a class which is callable, but also
        need it to have the argtypes and restype 
        parameters to match the calls made setting up the CCD. '''
    def __init__(self, func=None, st = '', retWeights = ()):
        self.argtypes = []
        self.restype = None
        self.st = st
        self.func = func
        # ((retchance1, retchance2, retchance3... ),
        #  (retval1,    retval2,    retval3))
        self.retWeights = retWeights
        
    def __call__(self, *args):
        log.debug("{}, {}".format(' '*10+self.st, args))
        self.func(args)
        ret = 20002
        # if not np.random.randint(5):
        #     ret = 20004
        if self.retWeights:
            ranges = np.cumsum(self.retWeights[0])
            rando = np.random.randint(ranges[-1])
            return self.retWeights[1][
                # Grab the first one where
                # it crosses over
                np.argwhere(rando<ranges)[0]
            ]
        """
        if self.st == "GetTemperature":
            n = np.random.randint(20)
            if n == 1:
                ret = 20036 # temp stabilized
            else:
                ret = 20037
        elif self.st == "Initialize":
            ret = -1
        elif self.st == 'InitializeMissingDLL':
            ret = -2
        """

        return ret

class fAndorEMCCD(object):
    def __init__(self):
        self.AbortAcquisition = myCallable(self.__voidReturn, 'AbortAcquisition')
        self.CancelWait = myCallable(self.__voidReturn, 'CancelWait')
        self.CoolerON = myCallable(self.__voidReturn, 'CoolerON')
        self.CoolerOFF = myCallable(self.__voidReturn, 'CoolerOFF')
        self.GetAcquiredData = myCallable(self.__getData, 'GetAcquiredData')
        self.GetCapabilities = myCallable(self.__voidReturn, 'GetCapabilities')
        self.GetDetector = myCallable(self.__getDet, 'GetDetector')
        self.GetHSSpeed = myCallable(self.__getHSS, 'GetHSSpeed')
        self.GetMostRecentImage = myCallable(self.__voidReturn, 'GetMostRecentImage')
        self.GetNumberADChannels = myCallable(self.__getNum, 'GetNumberADChannels')
        self.GetNumberHSSpeeds = myCallable(self.__getNum, 'GetNumberHSSpeeds')
        self.GetNumberVSSpeeds = myCallable(self.__getNum, 'GetNumberVSSpeeds')
        self.GetStatus = myCallable(self.__getNum, 'GetStatus')
        self.GetTemperature = myCallable(self.__getNum, 'GetTemperature', ((1, 20), (20036, 20037)))
        self.GetVSSpeed = myCallable(self.__getHSS, 'GetVSSpeed')
        self.Initialize = myCallable(self.__voidReturn, 'Initialize', ((1, ), (-1,)))
        self.PrepareAcquisition = myCallable(self.__voidReturn, 'PrepAcq')
        self.SetAcquisitionMode = myCallable(self.__voidReturn, 'SetAcqMode')
        self.SetADChannel = myCallable(self.__voidReturn, 'SetADChannel')
        self.SetCoolerMode = myCallable(self.__voidReturn, 'SetCoolerMode')
        self.SetEMCCDGain = myCallable(self.__voidReturn, 'SetEMCCDGain')
        self.SetExposureTime = myCallable(self.__setExp, 'SetExposureTime')
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
        self.WaitForAcquisition = myCallable(self.__wait, 'WaitForAqcuisition')

        
    def __voidReturn(self, *args):
        pass

    def __setImage(self, *args):
        pass

    def __getData(self, *args):
        arr = args[0][0]
        np.random.seed()
        new = [int(round(i)) for i in np.random.normal(297, 6, args[0][1])]
        big = [int(round(i))+np.random.randint(4500, 5200) for i in np.random.normal(297, 6, args[0][1])]
        # make non-sideband 1/5
        sidebanded = bool(np.random.randint(5))
        for i in range(args[0][1]):
            if sidebanded and i>1600*150 and i<1600*250:
                if (i-750)%1600==0:
                    arr[i] = int(big[i]/10)
                elif (i-749)%1600==0 or (i-751)%1600==0:
                    arr[i] = int(big[i]/14)
                elif (i-748)%1600==0 or (i-752)%1600==0:
                    arr[i] = int(big[i]/19)
                elif (i-500)%1600==0:
                    arr[i] = int(big[i])
                elif (i-499)%1600==0 or (i-501)%1600==0:
                    arr[i] = int(big[i]/1.6)
                elif (i-498)%1600==0 or (i-502)%1600==0:
                    arr[i] = int(big[i]/3)
                else:
                    if not np.random.randint(10000):
                        arr[i] = np.random.randint(3000, 30000)
                        arr[i-1] = int(0.8*arr[i])
                        arr[i-2] = int(0.72*arr[i])
                    else:
                        arr[i] = new[i]
            else:
                if not np.random.randint(10000):
                    arr[i] = np.random.randint(3000, 30000)
                    arr[i-1] = int(0.8*arr[i])
                    arr[i-2] = int(0.72*arr[i])
                else:
                    arr[i] = new[i]
            
    def __getDet(self, *args):
        x = args[0][0]
        y = args[0][1]
        x.value = 1600
        y.value = 400
        
    def __getHSS(self, *args):
        # print args
        x = args[0][-1]
        x.value = np.random.randint(100)
        x.value = 0.2 + args[0][-2] + len(args[0])*5
    
    def __getNum(self, *args):
        x = args[0][-1]
        x.value = np.random.randint(3, 5)
    def __cancelWait(self, *args):
        self.WaitForAcquisition.retWeights = ((1,), (20024,))
    def __wait(self, *args):
        # Wait a random amount of time to simulate it
        self.WaitForAcquisition.retWeights = ((1,), (20002,))
        print "Sleeping for: {}".format(self.exposure)
        time.sleep(self.exposure)

    def __setExp(self, val):
        self.exposure = val[0]
    
    

    
        



# a = fAndorEMCCD()



















































