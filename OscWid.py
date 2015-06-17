from PyQt4 import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
import scipy.integrate as spi
import re
from InstsAndQt.customQt import *
from InstsAndQt.Instruments import *
import visa
# import os, sys, inspect
# cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"UIs")))
# if cmd_subfolder not in sys.path:
#      sys.path.insert(0, cmd_subfolder)
from UIs.Oscilloscope_ui import Ui_Oscilloscope
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

import logging
log = logging.getLogger("EMCCD")


class OscWid(QtGui.QWidget):

    scopeCollectionThread = None # Thread which polls the scope
    scopePausingLoop = None # A QEventLoop which causes the scope collection
                            # thread to wait

    photonCountingThread = None # A thread whose only sad purpose
                                # in life is to wait for data to
                                # be emitted and to process
                                # and count it
    photonWaitingLoop = None # Loop while photon counting waits for more


    # Has the oscilloscope updated and data is now ready
    # for processing?
    updateOscDataSig = QtCore.pyqtSignal()
    # Can now update the graph
    pyDataSig = QtCore.pyqtSignal(object)

    # This will emit a dict of the values
    sigDoneCounting = QtCore.pyqtSignal()

    def __init__(self, papa = None):
        super(OscWid, self).__init__()
        self.initSettings()
        self.initUI()
        self.papa = papa # For keeping track of things relevant to the parent widget

        self.pyDataSig.connect(self.updateOscilloscopeGraph)
        self.photonCountingThread = TempThread(target = self.doPhotonCountingLoop)
        self.photonCountingThread.start()

        self.poppedPlotWindow = None

        self.openAgilent()

    def initSettings(self):
        s = dict()
        try:
            rm = visa.ResourceManager()
            ar = [i.encode('ascii') for i in rm.list_resources()]
            ar.append('Fake')
            s['GPIBlist'] = ar
        except:
            log.warning("Error loading GPIB list")
            ar = ['a', 'b', 'c', 'Fake']
            s['GPIBlist'] = ar
        try:
            # Pretty sure we can safely say it's
            # GPIB5
            idx = s['GPIBlist'].index('GPIB0::5::INSTR')
            s["agilGPIBidx"] = idx
        except ValueError:
            # otherwise, just set it to the fake index
            s["agilGPIBidx"] = s['GPIBlist'].index('Fake')

        # This will be used to toggle pausing on the scope
        s["isScopePaused"] = True
        # This flag will be used for safely terminating the
        # oscilloscope thread
        s["shouldScopeLoop"] = True
        s["doPhotonCounting"] = True
        s["exposing"] = False # For whether or not an exposure is happening

        # How many pulses are there?
        s["FELPulses"] = 0
        # list of the field intensities for each pulse in a scan
        s["fieldStrength"] = []
        s["fieldInt"] = []
        # lists for holding the boundaries of the linear regions
        s['bcpyBG'] = [0, 0]
        s['bcpyFP'] = [0, 0]
        s['bcpyCD'] = [0, 0]
        s['pyData'] = None

        self.settings = s

    def initUI(self):
        self.ui = Ui_Oscilloscope()
        self.ui.setupUi(self)

        ###################
        # Setting up oscilloscope values
        ##################
        self.ui.cOGPIB.addItems(self.settings['GPIBlist'])
        self.ui.cOGPIB.setCurrentIndex(self.settings["agilGPIBidx"])
        self.ui.bOPause.clicked[bool].connect(self.toggleScopePause)
        self.ui.cOGPIB.currentIndexChanged.connect(self.openAgilent)
        self.ui.bOscInit.clicked.connect(self.initOscRegions)
        self.ui.bOPop.clicked.connect(self.popoutOscilloscope)

        self.pOsc = self.ui.gOsc.plot(pen='k')
        plotitem = self.ui.gOsc.getPlotItem()
        plotitem.setTitle('Reference Detector')
        plotitem.setLabel('bottom',text='time scale',units='s')
        plotitem.setLabel('left',text='Voltage', units='V')

        #Now we make an array of all the textboxes for the linear regions to make it
        #easier to iterate through them. Set it up in memory identical to how it
        #appears on the panel for sanity, in a row-major fashion
        lrtb = [[self.ui.tBgSt, self.ui.tBgEn],
                [self.ui.tFpSt, self.ui.tFpEn],
                [self.ui.tCdSt, self.ui.tCdEn]]
        # Connect the changes to update the Linear Regions
        for i in lrtb:
            for j in i:
                j.textAccepted.connect(self.updateLinearRegionsFromText)

        self.linearRegionTextBoxes = lrtb
        self.initLinearRegions()
        self.show() #?

    @staticmethod
    def __ALL_THINGS_LINEARREGIONS(): pass

    def initLinearRegions(self, item = None):
        #initialize array for all 5 boxcar regions
        self.boxcarRegions = [None]*3

        bgCol = pg.mkBrush(QtGui.QColor(255, 0, 0, 50))
        fpCol = pg.mkBrush(QtGui.QColor(0, 0, 255, 50))
        sgCol = pg.mkBrush(QtGui.QColor(0, 255, 0, 50))

        #Background region for the pyro plot
        self.boxcarRegions[0] = pg.LinearRegionItem(self.settings['bcpyBG'], brush = bgCol)
        self.boxcarRegions[1] = pg.LinearRegionItem(self.settings['bcpyFP'], brush = fpCol)
        self.boxcarRegions[2] = pg.LinearRegionItem(self.settings['bcpyCD'], brush = sgCol)

        #Connect it all to something that will update values when these all change
        for i in self.boxcarRegions:
            i.sigRegionChangeFinished.connect(self.updateLinearRegionValues)

        if item is None:
            item = self.ui.gOsc
        item.addItem(self.boxcarRegions[0])
        item.addItem(self.boxcarRegions[1])
        item.addItem(self.boxcarRegions[2])



    def initOscRegions(self):
        try:
            length = len(self.settings['pyData'])
            point = self.settings['pyData'][length/2,0]
        except Exception as e:
            log.warning("Error initializing scope regions {}".format(e))
            return

        # Update the dicionary values so that the bounds are proper when
        d = {0: "bcpyBG",
             1: "bcpyFP",
             2: "bcpyCD"
        }
        for i in range(len(self.boxcarRegions)):
            self.boxcarRegions[i].setRegion(tuple((point, point)))
            self.settings[d[i]] = list((point, point))


    def updateLinearRegionValues(self):
        sender = self.sender()
        sendidx = -1
        for (i, v) in enumerate(self.boxcarRegions):
            #I was debugging something. I tried to use id(), which is effectively the memory
            #location to try and fix it. Found out it was anohter issue, but
            #id() seems a little safer(?) than just equating them in the sense that
            #it's explicitly asking if they're the same object, isntead of potentially
            #calling some weird __eq__() pyqt/graph may have set up
            if id(sender) == id(v):
                sendidx = i
        i = sendidx
        #Just being paranoid, no reason to think it wouldn't find the proper thing
        if sendidx<0:
            return
        self.linearRegionTextBoxes[i][0].setText('{:.9g}'.format(sender.getRegion()[0]))
        self.linearRegionTextBoxes[i][1].setText('{:.9g}'.format(sender.getRegion()[1]))

        # Update the dicionary values so that the bounds are proper when
        d = {0: "bcpyBG",
             1: "bcpyFP",
             2: "bcpyCD"
        }
        self.settings[d[i]] = list(sender.getRegion())

    def updateLinearRegionsFromText(self):
        sender = self.sender()
        #figure out where this was sent
        sendi, sendj = -1, -1
        for (i, v)in enumerate(self.linearRegionTextBoxes):
            for (j, w) in enumerate(v):
                if id(w) == id(sender):
                    sendi = i
                    sendj = j

        i = sendi
        j = sendj
        curVals = list(self.boxcarRegions[i].getRegion())
        curVals[j] = float(sender.text())
        self.boxcarRegions[i].setRegion(tuple(curVals))
        # Update the dicionary values so that the bounds are proper when
        d = {0: "bcpyBG",
             1: "bcpyFP",
             2: "bcpyCD"
        }
        self.settings[d[i]] = list(curVals)

    @staticmethod
    def __POPPING_OUT_CONTROLS(): pass

    def popoutOscilloscope(self):
        if self.poppedPlotWindow is None:
            self.poppedPlotWindow = BorderlessPgPlot()
            self.oldpOsc = self.pOsc
            for i in self.boxcarRegions:
                self.ui.gOsc.removeItem(i)
            self.pOsc = self.poppedPlotWindow.pw.plot(pen='k')
            plotitem = self.poppedPlotWindow.pw.getPlotItem()
            # plotitem.setLabel('bottom',text='time scale',units='s')
            plotitem.setLabel('left',text='Voltage', units='V')
            # I'd love to subclass the window further and figure out how to move it
            # by dragging on the outer edge of the plot...
            # self.poppedPlotWindow.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            self.poppedPlotWindow.show()
            # self.poppedPlotWindow.setWindowFlags(QtCore.Qt.WindowSystemMenuHint)
            self.poppedPlotWindow.closedSig.connect(self.cleanupCloseOsc)
            self.initLinearRegions(self.poppedPlotWindow.pw)
        else:
            self.poppedPlotWindow.raise_()

    def cleanupCloseOsc(self):
        self.poppedPlotWindow = None
        self.pOsc = self.oldpOsc
        self.initLinearRegions()

    @staticmethod
    def __OPEN_CONTROLLER(): pass

    def openAgilent(self, idx = None):
        self.settings["shouldScopeLoop"] = False
        isPaused = self.settings["isScopePaused"] # For intelligently restarting scope afterwards
        if isPaused:
            self.toggleScopePause(False)
        try:
            self.scopeCollectionThread.wait()
        except:
            pass
        try:
            self.Agilent.close()
        except Exception as e:
            log.warning("Error closing Agilent")
        try:
            self.Agilent = Agilent6000(
                self.settings["GPIBlist"][int(self.ui.cOGPIB.currentIndex())]
            )
        except Exception as e:
            log.warning( "Error opening Agilent, {}".format(e))
            self.Agilent = Agilent6000("Fake")
            # If you change the index programatically,
            # it signals again. But that calls this thread again
            # which really fucks up with the threading stuff
            # Cheap way is to just disconnect it and then reconnect it
            self.ui.cOGPIB.currentIndexChanged.disconnect()
            self.ui.cOGPIB.setCurrentIndex(
                self.settings["GPIBlist"].index("Fake")
            )
            self.ui.cOGPIB.currentIndexChanged.connect(self.openAgilent)

        self.Agilent.setTrigger()
        self.settings['shouldScopeLoop'] = True
        if isPaused:
            self.toggleScopePause(True)

        self.scopeCollectionThread = TempThread(target = self.collectScopeLoop)
        self.scopeCollectionThread.start()


    @staticmethod
    def __CONTROLLING_LOOPING(): pass
    def toggleScopePause(self, val):
        self.settings["isScopePaused"] = val
        if not val: # We want to stop any pausing thread if neceesary
            try:
                self.scopePausingLoop.exit()
            except:
                pass

    def collectScopeLoop(self):
        while self.settings['shouldScopeLoop']:
            if self.settings['isScopePaused']:
                #Have the scope updating remotely so it can be changed if needed
                self.Agilent.write(':RUN')
                #If we want to pause, make a fake event loop and terminate it from outside forces
                self.scopePausingLoop = QtCore.QEventLoop()
                self.scopePausingLoop.exec_()
                continue
            pyData = self.Agilent.getSingleChannel(int(self.ui.cOChannel.currentIndex())+1)
            if not self.settings['isScopePaused']:
                self.pyDataSig.emit(pyData)
                self.updateOscDataSig.emit()

    def doPhotonCountingLoop(self):
        while self.settings["doPhotonCounting"]:
            self.photonWaitingLoop = QtCore.QEventLoop()
            self.updateOscDataSig.connect(self.photonWaitingLoop.exit)
            self.photonWaitingLoop.exec_()
            if self.papa.curExp.runSettings["exposing"]:
                pyBG, pyFP, pyCD = self.integrateData()
                self.settings["pyBG"] = pyBG
                self.settings["pyFP"] = pyFP
                self.settings["pyCD"] = pyCD

                if (
                    (pyFP > pyBG * self.ui.tOscFPRatio.value()) and
                    (pyCD > pyBG * self.ui.tOscCDRatio.value())
                ):
                    self.settings["FELPulses"] += 1
                    self.papa.updateElementSig.emit(self.ui.tOscPulses, self.settings["FELPulses"])
                    self.papa.updateElementSig.emit(self.papa.curExp.ui.tCCDFELPulses, self.settings["FELPulses"])
                    # self.doFieldCalcuation(pyBG, pyFP, pyCD)
                    self.sigDoneCounting.emit()
                else:
                    print "PULSE NOT COUNTED!"


    @staticmethod
    def __INTEGRATING(): pass


    def integrateData(self):
        #Neater and maybe solve issues if the data happens to update
        #while trying to do analysis?
        pyD = self.settings['pyData']

        pyBGbounds = self.boxcarRegions[0].getRegion()
        pyBGidx = self.findIndices(pyBGbounds, pyD[:,0])

        pyFPbounds = self.boxcarRegions[1].getRegion()
        pyFPidx = self.findIndices(pyFPbounds, pyD[:,0])

        pyCDbounds = self.boxcarRegions[2].getRegion()
        pyCDidx = self.findIndices(pyCDbounds, pyD[:,0])

        pyBG = spi.simps(pyD[pyBGidx[0]:pyBGidx[1],1], pyD[pyBGidx[0]:pyBGidx[1], 0])
        pyFP = spi.simps(pyD[pyFPidx[0]:pyFPidx[1],1], pyD[pyFPidx[0]:pyFPidx[1], 0])
        pyCD = spi.simps(pyD[pyCDidx[0]:pyCDidx[1],1], pyD[pyCDidx[0]:pyCDidx[1], 0])

        return pyBG, pyFP, pyCD

    @staticmethod
    def findIndices(values, dataset):
        """Given an ordered dataset and a pair of values, returns the indices which
           correspond to these bounds  """
        indx = list((dataset>values[0]) & (dataset<values[1]))
        #convert to string for easy finding
        st = ''.join([str(int(i)) for i in indx])
        start = st.find('1')
        if start == -1:
            start = 0
        end = start + st[start:].find('0')
        if end<=0:
            end = 1
        return start, end


    def updateOscilloscopeGraph(self, data):
        self.settings['pyData'] = data
        self.pOsc.setData(data[:,0], data[:,1])

    def close(self):
        print "close"
        self.settings['shouldScopeLoop'] = False
        self.settings["doPhotonCounting"] = False
        #Stop pausing
        try:
            self.scopePausingLoop.exit()
        except:
            pass
        # Stop waiting for data
        try:
            self.photonWaitingLoop.exit()
        except:
            pass
        # Stop thread waiting for data
        try:
            self.waitingForDataLoop.exit()
        except:
            pass

        #Stop the runnign thread for collecting from scope
        try:
            self.scopeCollectionThread.wait()
        except:
            pass
        # Stop the thread which processing osc data
        try:
            self.photonCountingThread.wait()
        except:
            pass


        #Restart the scope to trigger as normal.
        try:
            self.Agilent.write(':RUN')
            self.Agilent.close()
        except AttributeError:
            pass
        if self.poppedPlotWindow is not None:
            self.poppedPlotWindow.close()


if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    ex = OscWid()
    sys.exit(app.exec_())