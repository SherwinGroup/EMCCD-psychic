# -*- coding: utf-8 -*-
"""
Created on Mon Feb 02 13:11:29 2015

@author: dvalovcin
"""

import numpy as np
import time

class SPEX(object):
    def __init__(self, GPIB_Number = None):
        self.instrument = None
        pass
    def write(self, command):
        try:
            self.instrument.write(command)
        except:
            print 'Error writting to instrument'
            
    def ask(self, commad):
        ret = False
        try:
            ret = self.instrument.ask(command)
        except:
            print 'Error asking question'
        return ret
        
    def writeS(self, command):
        ''' Function will automatically write the command
        to the SPEX and then write the O2000 command which transfers
        control back to the instr. Also adds the 0.5s delay suggested to 
        allow for internal timing'''
        self.write(command)
        self.write('O2000')
        time.sleep(0.5)
        
    def askS(self, command):
        pass