# -*- coding: utf-8 -*-
"""
Created on Sat Feb 14 15:06:30 2015

@author: Home
"""

import numpy as np
from PyQt4 import QtCore, QtGui
from mainWindow_ui import Ui_MainWindow
from Andor import AndorEMCCD
import pyqtgraph as pg
import scipy.integrate as spi
from image_spec_for_gui import EMCCD_image
from InstsAndQt.Instruments import *
import os
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
try:
    import visa
except:
    print 'GPIB VISA library not installed'
    raise
    
try:
    a = QtCore.QString()
except AttributeError:
    QtCore.QString = str
        

class TempThread(QtCore.QThread):
    """ Creates a QThread which will monitor the temperature changes in the
        CCD. Actually more general than that since it simply takes a function and some args...
    """
    def __init__(self, target, args = None):
        super(TempThread, self).__init__()
        self.target = target
        self.args = args

    def run(self):
        if self.args is None:
            self.target()
        else:
            self.target(self.args)

class pgPlot(QtGui.QMainWindow):
    """ Dirt simple class for a window
        that allows me to emit a signal wh en it's closed
    """
    closedSig = QtCore.pyqtSignal()
    def __init__(self, parent = None):
        super(pgPlot, self).__init__(parent)
        self.pw = pg.PlotWidget()
        self.setCentralWidget(self.pw)
        self.show()

    def closeEvent(self, event):
        self.closedSig.emit()
        event.accept()


class CCDWindow(QtGui.QMainWindow):
    # signal definitions
    updateElementSig = QtCore.pyqtSignal(object, object) # This can be used for updating any element
    killTimerSig = QtCore.pyqtSignal(object) # To kill a timer started in the main thread from a sub-thread
     # to update either image, whether it is clean or not
    updateDataSig = QtCore.pyqtSignal(object, object)
    # Has the oscilloscope updated and data is now ready
    # for processing?
    updateOscDataSig = QtCore.pyqtSignal()
    # Can now update the graph
    pyDataSig = QtCore.pyqtSignal(object)

    # Thread definitions
    setTempThread = None
    getTempTimer = None # Timer for updating the current temperature while the detector is warming/cooling

    getImageThread = None
    updateProgTimer = None # timer for updating the progress bar

    getContinuousThread = None # Thread for acquiring continuously

    scopeCollectionThread = None # Thread which polls the scope
    scopePausingLoop = None # A QEventLoop which causes the scope collection
                            # thread to wait

    photonCountingThread = None # A thread whose only sad purpose
                                # in life is to wait for data to
                                # be emitted and to process
                                # and count it
    photonWaitingLoop = None # Loop while photon counting waits for more

    def __init__(self):
        super(CCDWindow, self).__init__()
        self.initSettings()

        # instantiate the CCD class so that we can get values from it to
        # populate menus in the UI.
        try:
            self.CCD = AndorEMCCD()
        except TypeError:
            self.close()
        self.CCD.initialize()

        self.initUI()
        self.Spectrometer = None
        self.Agilent = None
        self.openSpectrometer()
        self.openAgilent()
        self.poppedPlotWindow = None

        self.updateElementSig.connect(self.updateUIElement)
        self.killTimerSig.connect(self.stopTimer)
        self.updateDataSig.connect(self.updateImage)
        self.pyDataSig.connect(self.updateOscilloscopeGraph)
        self.photonCountingThread = TempThread(target = self.doPhotonCountingLoop)
        self.photonCountingThread.start()

    def initSettings(self):
        s = dict() # A dictionary to keep track of miscellaneous settings

        # Get the GPIB instrument list
        try:
            rm = visa.ResourceManager()
            ar = [i.encode('ascii') for i in rm.list_resources()]
            ar.append('Fake')
            s['GPIBlist'] = ar
        except:
            print 'Error loading GPIB list'
            ar = ['a', 'b', 'c', 'Fake']
            s['GPIBlist'] = ar
        try:
            # Pretty sure we can safely say it's
            # ASRL1
            idx = s['GPIBlist'].index('ASRL1::INSTR')
            s["specGPIBidx"] = idx
        except ValueError:
            # otherwise, just set it to the fake index
            s["specGPIBidx"] = s['GPIBlist'].index('Fake')
        try:
            # Pretty sure we can safely say it's
            # ASRL1
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
        s['pyData'] = None
        # lists for holding the boundaries of the linear regions
        s['bcpyBG'] = [0, 0]
        s['bcpyFP'] = [0, 0]
        s['bcpyCD'] = [0, 0]

        # Which settings combo boxes have been changed?
        # AD, VSS, Read, HSS, Trigg, Acq, intShutter, exShutter
        s["changedSettingsFlags"] = [0, 0, 0, 0, 0, 0, 0, 0]

        # Which image boxes have been changed?
        # HBin, VBin, HSt, HEn, VSt, VEn
        s["changedImageFlags"] = [0, 0, 0, 0, 0, 0] # Flags for when we change the
                                                                # image settings.
        s["settingsUI"] = None # Keep track of the settings comboboxes for iteration
        s["imageUI"] = None # keep ttrack of the settings param textedits for iteration
        s["isImage"] = True # Is it an image read mode?

        s["saveDir"] = '' # Directory for saving

        # For Hunter. First time you set a temp, it will
        # pop up and make sure you turned on the chiller
        s['askedChiller'] = False

        #Current image and background
        self.curData = None
        s["igNumber"] = 0
        self.curBG = None
        s["bgNumber"] = 0

        # These are for the EMCCD classes which will
        # clean/save/process the data
        self.curDataEMCCD = None
        self.curBGEMCCD = None

        # The current value contaiend in the progress bar
        s["progress"] = 0
        self.killFast = False

        # do you want me to remove cosmic rays?
        s["doCRR"] = True
        s["takeContinuous"] = False

        self.settings = s

    def initUI(self):
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # I don't want some of the buttons in the Acquisition mode to be clickable, because they're not
        # valid settings. But I want them there so that I can just call the <combobox>.currentindex() wihtout
        # having to do some trickery to find out the index and corresponding proper index with relation to the
        # andor.
        # http://stackoverflow.com/questions/11099975/pyqt-set-enabled-property-of-a-row-of-qcombobox
        disable = [0, 6, 7, 8]
        for i in disable:
            j = self.ui.cSettingsAcquisitionMode.model().index(i, 0)
            try:
                self.ui.cSettingsAcquisitionMode.model().setData(j, QtCore.QVariant(0), QtCore.Qt.UserRole-1)
            except TypeError:
                self.ui.cSettingsAcquisitionMode.model().setData(j, 0, QtCore.Qt.UserRole-1)


        # Updating menus in the settings/CCD settings portion
        self.ui.cSettingsADChannel.addItems([str(i) for i in range(
            self.CCD.cameraSettings['numADChannels'])])

        #####################
        # Setting the Speeds and image settings
        ###################
        self.ui.cSettingsVSS.addItems([str(i) for i in self.CCD.cameraSettings['VSS']])
        self.ui.cSettingsHSS.addItems([str(i) for i in self.CCD.cameraSettings['HSS']])
        self.ui.tHBin.setText(str(self.CCD.cameraSettings['imageSettings'][0]))
        self.ui.tVBin.setText(str(self.CCD.cameraSettings['imageSettings'][1]))
        self.ui.tHStart.setText(str(self.CCD.cameraSettings['imageSettings'][2]))
        self.ui.tHEnd.setText(str(self.CCD.cameraSettings['imageSettings'][3]))
        self.ui.tVStart.setText(str(self.CCD.cameraSettings['imageSettings'][4]))
        self.ui.tVEnd.setText(str(self.CCD.cameraSettings['imageSettings'][5]))

        ################
        # Connect all of the setting changes
        ###############
        self.ui.cSettingsReadMode.currentIndexChanged[QtCore.QString].connect(self.parseSettingsChange)
        self.ui.cSettingsADChannel.currentIndexChanged[QtCore.QString].connect(self.parseSettingsChange)
        self.ui.cSettingsVSS.currentIndexChanged[QtCore.QString].connect(self.parseSettingsChange)
        self.ui.cSettingsHSS.currentIndexChanged[QtCore.QString].connect(self.parseSettingsChange)
        self.ui.cSettingsTrigger.currentIndexChanged[QtCore.QString].connect(self.parseSettingsChange)
        self.ui.cSettingsAcquisitionMode.currentIndexChanged[QtCore.QString].connect(self.parseSettingsChange)
        self.ui.cSettingsShutter.currentIndexChanged[QtCore.QString].connect(self.parseSettingsChange)
        self.ui.cSettingsShutterEx.currentIndexChanged[QtCore.QString].connect(self.parseSettingsChange)
        self.ui.tImageName.editingFinished.connect(self.makeSpectraFolder)

        ####################
        # Create a list of the ui setting handles for iteration
        ###################
        self.settings["settingsUI"] = [self.ui.cSettingsADChannel,
                                       self.ui.cSettingsVSS,
                                       self.ui.cSettingsReadMode,
                                       self.ui.cSettingsHSS,
                                       self.ui.cSettingsTrigger,
                                       self.ui.cSettingsAcquisitionMode,
                                       self.ui.cSettingsShutter,
                                       self.ui.cSettingsShutterEx]

        #########################
        # Connect all of the changes to the image parameters
        #########################
        self.ui.tHBin.textAccepted[object].connect(self.parseImageChange)
        self.ui.tHStart.textAccepted[object].connect(self.parseImageChange)
        self.ui.tHEnd.textAccepted[object].connect(self.parseImageChange)
        self.ui.tVBin.textAccepted[object].connect(self.parseImageChange)
        self.ui.tVStart.textAccepted[object].connect(self.parseImageChange)
        self.ui.tVEnd.textAccepted[object].connect(self.parseImageChange)

        ######################
        # Array of setting changes for easy iteration
        #####################
        self.settings["imageUI"] = [self.ui.tHBin,
                                    self.ui.tVBin,
                                    self.ui.tHStart,
                                    self.ui.tHEnd,
                                    self.ui.tVStart,
                                    self.ui.tVEnd]

        ######################
        # Setting up spectrometer UI elements
        ######################
        self.ui.cSpecGPIB.addItems(self.settings['GPIBlist'])
        self.ui.cSpecGPIB.setCurrentIndex(self.settings["specGPIBidx"])
        self.ui.cSpecGPIB.currentIndexChanged.connect(self.SpecGPIBChanged)
        self.ui.bSpecSetWl.clicked.connect(self.updateSpecWavelength)
        self.ui.bSpecSetGr.clicked.connect(self.updateSpecGrating)

        ###################
        # Setting up oscilloscope values
        ##################
        self.ui.cOGPIB.addItems(self.settings['GPIBlist'])
        self.ui.cOGPIB.setCurrentIndex(self.settings["agilGPIBidx"])
        self.ui.bOPause.clicked[bool].connect(self.toggleScopePause)
        self.ui.cOGPIB.currentIndexChanged.connect(self.openAgilent)
        self.ui.bOPop.clicked.connect(self.popoutOscilloscope)

        self.pOsc = self.ui.gOsc.plot(pen='k')
        plotitem = self.ui.gOsc.getPlotItem()
        plotitem.setLabel('top',text='Reference Detector')
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
                                    
        ####################
        # Connect more things
        ###################
        self.ui.cSettingsVSS.setCurrentIndex(1)
        self.ui.bSettingsApply.setEnabled(False)
        self.ui.bSettingsApply.clicked.connect(self.updateSettings)
        self.ui.bSettingsCancel.clicked.connect(self.cancelSettings)
        self.ui.bSetTemp.clicked.connect(self.doTempSet)
        self.ui.bCCDImage.clicked.connect(lambda: self.startTakeImage("img"))
        self.ui.bCCDBack.clicked.connect(lambda: self.startTakeImage("bg"))

        ####################
        # Save file connection
        ##################
        self.ui.bSettingsDirectory.clicked.connect(self.chooseSaveDir)
        self.ui.tSettingsDirectory.setEnabled(False)

        ##################
        # Connections for updating image counters when user-changed
        ##################
        self.ui.tCCDImageNum.textAccepted.connect(
            lambda: self.updateImageNumbers(True))
        self.ui.tCCDBGNum.textAccepted.connect(
            lambda: self.updateImageNumbers(False))

        ##################
        # Connections for file menu things
        ##################
        # All I want it to do is set a flag which gets checked later.
        self.ui.mFileDoCRR.triggered[bool].connect(lambda v: self.settings.__setitem__('doCRR', v))
        self.ui.mFileBreakTemp.triggered.connect(lambda: self.setTempThread.terminate())
        self.ui.mFileTakeContinuous.triggered[bool].connect(self.startTakeContinuous)

        # Follow the pyqtgraph example for how to set up
        # an image plot and histogram, without the other obnoxious stuff
        # included in a plain ImageView
        self.p1 = self.ui.gCCDImage.addPlot()
        self.pSigImage = pg.ImageItem()
        self.p1.addItem(self.pSigImage)
        self.pSigHist = pg.HistogramLUTItem()
        self.pSigHist.setImageItem(self.pSigImage)
        self.ui.gCCDImage.addItem(self.pSigHist)

        self.p2 = self.ui.gCCDBack.addPlot()
        self.pBackImage = pg.ImageItem()
        self.p2.addItem(self.pBackImage)
        self.pBackHist = pg.HistogramLUTItem()
        self.pBackHist.setImageItem(self.pBackImage)
        self.ui.gCCDBack.addItem(self.pBackHist)

        self.pSpec = self.ui.gCCDBin.plot(pen='k')
        plotitem = self.ui.gCCDBin.getPlotItem()
        plotitem.setLabel('top',text='Spectrum')
        plotitem.setLabel('bottom',text='Wavelength',units='nm')
        plotitem.setLabel('left',text='Counts')

        self.show()

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

    def popoutOscilloscope(self):
        if self.poppedPlotWindow is None:
            self.poppedPlotWindow = pgPlot()
            self.oldpOsc = self.pOsc
            for i in self.boxcarRegions:
                self.ui.gOsc.removeItem(i)
            self.pOsc = self.poppedPlotWindow.pw.plot(pen='k')
            plotitem = self.poppedPlotWindow.pw.getPlotItem()
            plotitem.setLabel('top',text='Reference Detector')
            plotitem.setLabel('bottom',text='time scale',units='s')
            plotitem.setLabel('left',text='Voltage', units='V')
            self.poppedPlotWindow.closedSig.connect(self.cleanupCloseOsc)
            self.initLinearRegions(self.poppedPlotWindow.pw)
        else:
            self.poppedPlotWindow.raise_()

    def cleanupCloseOsc(self):
        self.poppedPlotWindow = None
        self.pOsc = self.oldpOsc
        self.initLinearRegions()

    def SpecGPIBChanged(self):
        self.Spectrometer.close()
        self.settings["specGPIBidx"] = int(self.ui.cSpecGPIB.currentIndex())
        self.openSpectrometer()

    # def AgilGPIBChanged(self):
    #     self.settings[]
    #     self.openAgilent()

    def openSpectrometer(self):
        # THIS should really be in a try:except: loop for if
        # the spec timeouts or cant be connected to
        self.Spectrometer = ActonSP(
            self.settings["GPIBlist"][self.settings["specGPIBidx"]]
        )
        self.ui.tSpecCurWl.setText(str(self.Spectrometer.getWavelength()))
        self.ui.sbSpecWavelength.setValue(self.Spectrometer.getWavelength())
        self.ui.tSpecCurGr.setText(str(self.Spectrometer.getGrating()))
        self.ui.sbSpecGrating.setValue(self.Spectrometer.getWavelength())

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
            print "__main__.openAgilent:\nError closing Agilent,",e
        try:
            self.Agilent = Agilent6000(
                self.settings["GPIBlist"][int(self.ui.cOGPIB.currentIndex())]
            )
            print 'Agilent opened'
        except Exception as e:
            print "__main__.openAgilent:\nError opening Agilent,",e
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

    def toggleScopePause(self, val):
        print "Toggle scope. val={}".format(val)
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
            if self.settings["exposing"]:
                pyBG, pyFP, pyCD = self.integrateData()
                if (
                    (pyFP > pyBG * self.ui.tOscFPRatio.value()) and
                    (pyCD > pyBG * self.ui.tOscCDRatio.value())
                ):
                    print "PULSE COUNTED!"
                    self.settings["FELPulses"] += 1
                    self.updateElementSig.emit(self.ui.tOscPulses, self.settings["FELPulses"])
                    self.updateElementSig.emit(self.ui.tCCDFELPulses, self.settings["FELPulses"])
                else:
                    print "PULSE NOT COUNTED!"


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

    def findIndices(self, values, dataset):
        '''Given an ordered dataset and a pair of values, returns the indices which
           correspond to these bounds  '''
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

    def updateSpecWavelength(self):
        desired = float(self.ui.sbSpecWavelength.value())
        new = self.Spectrometer.goAndAsk(desired)
        self.ui.tSpecCurWl.setText(str(new))

    def updateSpecGrating(self):
        desired = int(self.ui.sbSpecGrating.value())
        self.Spectrometer.setGrating(desired)
        new = self.Spectrometer.getGrating()
        self.ui.tSpecCurGr.setText(str(new))

    def updateImageNumbers(self, isIm = True):
        """
        :param sender: flag for who sent
        :return:
        allow the user to update the image number counters
        """
        if isIm:
            self.settings["igNumber"] = int(self.ui.tCCDImageNum.text())
        else:
            self.settings["bgNumber"] = int(self.ui.tCCDBGNum.text())

    def parseImageChange(self, st):
        sent = self.sender()

        idx = self.settings['imageUI'].index(sent)

        if int(st) == self.CCD.cameraSettings['imageSettings'][idx]:
            self.settings["changedImageFlags"][idx] = 0
        else:
            self.settings["changedImageFlags"][idx] = 1

        # Check to see if anything was changed in these settings or in the
        # text boxes for the Image settings.
        if 1 in np.append(self.settings["changedSettingsFlags"],
                          self.settings["changedImageFlags"]):
            self.ui.bSettingsApply.setEnabled(True)
        else:
            self.ui.bSettingsApply.setEnabled(False)

    def parseSettingsChange(self, st):
        """ I like to be fancy. I want the apply button to dis-enable when you've reselected
        an option that will be the same"""
        sent = self.sender()

        idx = self.settings["settingsUI"].index(sent)

        # Make a list of values from the CCD settings dictionary which have 'cur'
        # in it. Then check to see if the value which one combo box was changed to
        # in this list, meaning something was changed back. If it was changed back,
        # set that part of the flags array to 0, else signify is was changed to something
        # new.
        #
        # Will cause errors if ever have the same VSS/HSS. Or other complications when
        # there are CCD.cameraSettings which have the key 'cur'
        if st in [str(i) for i in
                  [self.CCD.cameraSettings[k] for k in
                   self.CCD.cameraSettings.keys() if 'cur' in k]]:
            self.settings["changedSettingsFlags"][idx] = 0
        else:
            self.settings["changedSettingsFlags"][idx] = 1

        if idx == 2 and st != "Image":
            self.ui.gbImageParams.setEnabled(False)
            self.settings["isImage"] = False
        elif idx == 2:
            self.ui.gbImageParams.setEnabled(True)
            self.settings["isImage"] = True
        # Error above mentioned about identical settings has to be handled for the shutter,
        # as both share the same names
        # 
        # Here it is for the first shutter
        elif idx == 6:
            if st == self.CCD.cameraSettings["curShutterInt"]:
                self.settings["changedSettingsFlags"][idx] = 0
            else:
                self.settings["changedSettingsFlags"][idx] = 1
        elif idx == 7:
            if st == self.CCD.cameraSettings["curShutterEx"]:
                self.settings["changedSettingsFlags"][idx] = 0
            else:
                self.settings["changedSettingsFlags"][idx] = 1
            
                
            
        
        

        # Check to see if anything was changed in these settings or in the
        # text boxes for the Image settings.
        if 1 in np.append(self.settings["changedSettingsFlags"],
                          self.settings["changedImageFlags"]):
            self.ui.bSettingsApply.setEnabled(True)
        else:
            self.ui.bSettingsApply.setEnabled(False)

    def updateSettings(self):
        changed = self.settings["changedSettingsFlags"] # Don't want to keep typing this

        # AD channel has been changed. Extra care must be taken because
        # this means the HSS has also been changed
        if changed[0] == 1:
            ret = self.CCD.setAD(int(self.ui.cSettingsADChannel.currentText()))
            print 'Change AD Channel: {}'.format(self.CCD.parseRetCode(ret))
            if ret != 20002:
                print 'Bad return'
                return

            # Changing the AD changes the available HSS. Find out what they are,
            # update the list of choices. Then change HSS to the first value
            self.CCD.getHSS()
            self.ui.cSettingsHSS.clear()
            self.ui.cSettingsHSS.addItems([str(i) for i in self.CCD.cameraSettings['HSS']])
            ret = self.CCD.setHSS(0)
            print 'Change HSS, AD: {}'.format(self.CCD.parseRetCode(ret))
            self.ui.cSettingsHSS.setCurrentIndex(0)

            # Unflag for change of AD
            self.settings["changedSettingsFlags"][0] = 0
            # Unflag change of HSS (we don't care what you previously wanted, it's likely not
            # there anymore.
            self.settings["changedSettingsFlags"][3] = 0

        # The VSS has changed
        if changed[1] == 1:
            ret = self.CCD.setVSS(int(self.ui.cSettingsVSS.currentIndex()))
            print 'Change VSS: {}'.format(self.CCD.parseRetCode(ret))
            self.settings["changedSettingsFlags"][1] = 0


        # Read mode has changed
        if changed[2] == 1:
            ret = self.CCD.setRead(self.ui.cSettingsReadMode.currentIndex())
            print "Changed Read mode: {}".format(self.CCD.parseRetCode(ret))
            self.settings["changedSettingsFlags"][2] = 0

        # HSS Changed
        if changed[3] == 1:
            ret = self.CCD.setHSS(self.ui.cSettingsHSS.currentIndex())
            print "Changed HSS: {}".format(self.CCD.parseRetCode(ret))
            self.settings["changedSettingsFlags"][3] = 0

        # Trigger mode changed
        if changed[4] == 1:
            ret = self.CCD.setTrigger(self.ui.cSettingsTrigger.currentIndex())
            print 'Changed Trigger: {}'.format(self.CCD.parseRetCode(ret))
            self.settings["changedSettingsFlags"][4] = 0

        # changed Acquisition mode
        if changed[5] == 1:
            ret = self.CCD.setAcqMode(self.ui.cSettingsAcquisitionMode.currentIndex())
            print 'Changed Acq: {}'.format(self.CCD.parseRetCode(ret))
            self.settings["changedSettingsFlags"][5] = 0

        # Did either of the shutter values changed
        if 1 in changed[6:8]:
            ret = self.CCD.setShutterEx(
                self.ui.cSettingsShutter.currentIndex(),
                self.ui.cSettingsShutterEx.currentIndex()
            )
            print 'Changed shutter: {}'.format(self.CCD.parseRetCode(ret))
            self.settings["changedSettingsFlags"][6:8] = [0, 0]


        # Now change the settings parameters
        if 1 in self.settings["changedImageFlags"]:
            # Get the array to change to
            vals = [int(i.text()) for i in self.settings["imageUI"]]
            ret = self.CCD.setImage(vals)
            print "Changed image: {}".format(self.CCD.parseRetCode(ret))
            self.settings["changedImageFlags"] = [0, 0, 0, 0, 0, 0]

        self.ui.bSettingsApply.setEnabled(False)

    def cancelSettings(self):
        self.ui.cSettingsADChannel.setCurrentIndex(
            self.CCD.cameraSettings['curADChannel'])

        idx = self.ui.cSettingsVSS.findText(str(self.CCD.cameraSettings['curVSS']))
        self.ui.cSettingsVSS.setCurrentIndex(idx)

        idx = self.ui.cSettingsReadMode.findText(str(self.CCD.cameraSettings['curReadMode']))
        self.ui.cSettingsReadMode.setCurrentIndex(idx)

        idx = self.ui.cSettingsHSS.findText(str(self.CCD.cameraSettings['curHSS']))
        self.ui.cSettingsHSS.setCurrentIndex(idx)

        idx = self.ui.cSettingsTrigger.findText(str(self.CCD.cameraSettings['curTrig']))
        self.ui.cSettingsTrigger.setCurrentIndex(idx)

        idx = self.ui.cSettingsAcquisitionMode.findText(str(self.CCD.cameraSettings['curAcqMode']))
        self.ui.cSettingsAcquisitionMode.setCurrentIndex(idx)

        idx = self.ui.cSettingsShutter.findText(str(self.CCD.cameraSettings["curShutterInt"]))
        self.ui.cSettingsShutter.setCurrentIndex(idx)

        idx = self.ui.cSettingsShutterEx.findText(str(self.CCD.cameraSettings["curShutterEx"]))
        self.ui.cSettingsShutterEx.setCurrentIndex(idx)

        for (i, uiEle) in enumerate(self.settings["imageUI"]):
            uiEle.setText(str(self.CCD.cameraSettings['imageSettings'][i]))

    def chooseSaveDir(self):
        prevDir = self.settings["saveDir"]
        hint = "Choose save directory..."
        filen = str(QtGui.QFileDialog.getExistingDirectory(self, hint, prevDir))
        if filen == '':
            return
        print "filename: {}".format(filen)
        #Update the appropriate file
        self.settings["saveDir"] = filen
        self.ui.tSettingsDirectory.setText(filen)

        #create the appropriate folders
        newIm = os.path.join(filen, 'Images')
        newSpec = os.path.join(filen, 'Spectra')

        # See if the folders exists and try to make them if they don't
        if not os.path.exists(newIm):
            try:
                os.mkdir(newIm)
            except:
                print "Failed creating new image directory, {}".format(newIm)

        if not os.path.exists(newSpec):
            try:
                os.mkdir(newSpec)
            except:
                print "Failed creating new spectra directory, {}".format(newSpec)

        # Changed the path, want to make a new spectrum folder for the current
        # name. That is, unless it's the default name, which likely means
        # the user just started up and changed the dir
        if str(self.ui.tImageName.text()) != "test":
            self.makeSpectraFolder()

    def makeSpectraFolder(self):
        specFold = os.path.join(self.settings["saveDir"],
                                'Spectra', str(self.ui.tImageName.text()))
        if not os.path.exists(specFold):
            try:
                os.mkdir(specFold)
            except Exception as e:
                st = "__main__.makeSpectraFolder\n\tFailed to make folder for spectrum, {}\n\tReason given as {}"
                print st.format(specFold)

    def doTempSet(self, temp = None):
        # temp is so that it can be called during cleanup.
        if not self.settings['askedChiller']:
            self.settings['askedChiller'] = True
            self.dump = ChillerBox(self, "Did you turn on the chiller?")
            self.dump.show()

            # Set up a timer to destroy the window after some time.
            # Really, letting python garbage collecting take care of it
            QtCore.QTimer.singleShot(3000, lambda: setattr(self, "dump", None))
            QtCore.QTimer.singleShot(3000, lambda: self.dump.close())
#        if temp is None:
        temp = int(self.ui.tSettingsGotoTemp.text())

        # Disable the buttons we don't want messed with
        self.ui.bCCDBack.setEnabled(False)
        self.ui.bCCDImage.setEnabled(False)
        self.ui.bSetTemp.setEnabled(False)

        # Set up a thread which will handle the monitoring of the temperature
        self.setTempThread = TempThread(target = self.CCD.gotoTemperature, args = (temp, self.killFast))
        self.setTempThread.finished.connect(self.cleanupSetTemp)
        # This timer will update the UI with the changes in temperature
        self.getTempTimer = QtCore.QTimer(self)
        self.getTempTimer.timeout.connect(self.updateTemp)
        self.getTempTimer.start(1000)
        self.setTempThread.start()
        self.ui.mFileBreakTemp.setEnabled(True)

    def cleanupSetTemp(self):
        self.ui.mFileBreakTemp.setEnabled(False)
        self.ui.bCCDImage.setEnabled(True)
        self.ui.bCCDBack.setEnabled(True)
        self.ui.bSetTemp.setEnabled(True)
        self.getTempTimer.stop()

        self.updateTemp()

    def updateTemp(self):
        self.ui.tSettingsCurrTemp.setText(str(self.CCD.temperature))
        self.ui.tSettingsTempResponse.setText(self.CCD.tempRetCode)

    def startTakeImage(self, imtype = "img"):
        self.ui.bCCDImage.setEnabled(False)
        self.ui.bCCDBack.setEnabled(False)
        self.ui.gbSettings.setEnabled(False)
        self.settings["progress"] = 0
        self.settings["FELPulses"] = 0
        self.ui.tOscPulses.setText("0")
        self.getImageThread = TempThread(target = self.takeImage, args=imtype)

        # Update exposure/gain if necesssary
        if not np.isclose(float(self.ui.tEMCCDExp.text()), self.CCD.cameraSettings["exposureTime"]):
            self.CCD.setExposure(float(self.ui.tEMCCDExp.text()))
        if not int(self.ui.tEMCCDGain.text()) == self.CCD.cameraSettings["gain"]:
            self.CCD.setGain(int(self.ui.tEMCCDGain.text()))

        # self.updateProgTimer = QtCore.QTimer()
        # self.updateProgTimer.timeout.connect(self.updateProgress)
        # self.updateProgTimer.start(self.CCD.cameraSettings["exposureTime"]*10)

        self.elapsedTimer = QtCore.QElapsedTimer()
        if self.settings["isScopePaused"]:
            self.settings["exposing"] = True
            self.elapsedTimer.start()
            QtCore.QTimer.singleShot(self.CCD.cameraSettings["exposureTime"]*10,
                                     self.updateProgress)
        else:
            self.updateOscDataSig.connect(self.startProgressBar)
        self.getImageThread.start()
        
    def startProgressBar(self):
        self.settings["exposing"] = True
        self.elapsedTimer.start()
        QtCore.QTimer.singleShot(self.CCD.cameraSettings["exposureTime"]*10,
                                 self.updateProgress)
        self.updateOscDataSig.disconnect(self.startProgressBar)
        

    def takeImage(self, imtype):
        """
        Want to have the exposing flags set here just so there's no funny business
        Sometimes the other thread may msibehave and we don't want photons to keep on
        counting
        """
        self.settings["exposing"] = True
        self.updateElementSig.emit(self.ui.lCCDProg, "Waiting exposure")
        self.CCD.dllStartAcquisition()
        self.CCD.dllWaitForAcquisition()
        self.settings["exposing"] = False
        # self.killTimerSig.emit(self.updateProgTimer)
        data = self.CCD.getImage()

        if imtype=="img":
            self.curData = data
            self.updateDataSig.emit(True, False)
            self.settings["igNumber"] += 1
            self.updateElementSig.emit(self.ui.tCCDImageNum, self.settings["igNumber"])
        else:
            self.curBG = data
            self.updateDataSig.emit(False, False)
            self.settings["bgNumber"] += 1
            self.updateElementSig.emit(self.ui.tCCDBGNum, self.settings["bgNumber"])

        self.updateElementSig.emit(self.ui.lCCDProg, "Cleaning Data")


        if imtype=="img":
            self.curDataEMCCD = EMCCD_image(self.curData,
                                            str(self.ui.tImageName.text()),
                                            str(self.ui.tCCDImageNum.text()),
                                            str(self.ui.tCCDComments.toPlainText()),
                                            self.genEquipmentDict())
            try:
                self.curDataEMCCD.save_images(self.settings["saveDir"])
            except Exception as e:
                print "Error saving data image", e

            if self.settings["doCRR"]:
                try:
                    self.curDataEMCCD.cosmic_ray_removal()
                except Exception as e:
                    print "cosmic,",e
            else:
                self.curDataEMCCD.clean_array = self.curDataEMCCD.raw_array

            try:
                self.curDataEMCCD = self.curDataEMCCD - self.curBGEMCCD
            except Exception as e:
                print 'subraction:', e

            try:
                self.curDataEMCCD.make_spectrum()
            except Exception as e:
                print e
            try:
                self.curDataEMCCD.save_spectrum(self.settings["saveDir"])
            except Exception as e:
                print "__main__.takeImage\nError saving spectrum,",e
            self.updateDataSig.emit(True, True) # update with the cleaned data
        else:
            self.curBGEMCCD = EMCCD_image(self.curBG,
                                            str(self.ui.tBackgroundName.text()),
                                            str(self.ui.tCCDBGNum.text()),
                                            str(self.ui.tCCDComments.toPlainText()),
                                            self.genEquipmentDict())
            try:
                self.curBGEMCCD.save_images(self.settings["saveDir"])
            except Exception as e:
                print "__main__.takeImage\nError saving background iamge", e

            if self.settings["doCRR"]:
                self.curBGEMCCD.cosmic_ray_removal()
            else:
                self.curBGEMCCD.clean_array = self.curBGEMCCD.raw_array

            self.curBGEMCCD.make_spectrum()
            self.updateDataSig.emit(False, True) # update with the cleaned data

        self.updateElementSig.emit(self.ui.lCCDProg, "Done.")
        self.ui.bCCDImage.setEnabled(True)
        self.ui.bCCDBack.setEnabled(True)
        self.ui.gbSettings.setEnabled(True)

    def startTakeContinuous(self, val):
        if val is True:
        # Update exposure/gain if necesssary
            if not np.isclose(float(self.ui.tEMCCDExp.text()), self.CCD.cameraSettings["exposureTime"]):
                self.CCD.setExposure(float(self.ui.tEMCCDExp.text()))
            if not int(self.ui.tEMCCDGain.text()) == self.CCD.cameraSettings["gain"]:
                self.CCD.setGain(int(self.ui.tEMCCDGain.text()))
            self.ui.gbSettings.setEnabled(False)
            self.ui.bCCDBack.setEnabled(False)
            self.ui.bCCDImage.setEnabled(False)
            self.getContinuousThread = TempThread(target = self.takeContinuous)
            self.getContinuousThread.start()

    def takeContinuous(self):
        while self.ui.mFileTakeContinuous.isChecked():
            self.CCD.dllStartAcquisition()
            self.CCD.dllWaitForAcquisition()
            self.curData = self.CCD.getImage()
            self.updateDataSig.emit(True, False)

        self.ui.gbSettings.setEnabled(True)
        self.ui.bCCDBack.setEnabled(True)
        self.ui.bCCDImage.setEnabled(True)


    def genEquipmentDict(self):
        """
        The EMCCD class wants a specific dictionary of values. This function will return it
        :return:
        """
        s = dict()
        s["CCD_temperature"] = str(self.ui.tSettingsCurrTemp.text())
        s["exposure"] = float(self.CCD.cameraSettings["exposureTime"])
        s["gain"] = int(self.CCD.cameraSettings["gain"])
        s["y_min"] = int(self.ui.tCCDYMin.text())
        s["y_max"] = int(self.ui.tCCDYMax.text())
        s["grating"] = int(self.ui.sbSpecGrating.value())
        s["center_lambda"] = float(self.ui.sbSpecWavelength.value())
        s["slits"] = str(self.ui.tCCDSlits.text())
        s["dark_region"] = None
        s["bg_file_name"] = str(self.ui.tBackgroundName.text()) + str(self.ui.tCCDBGNum.text())
        s["NIRP"] = str(self.ui.tCCDNIRP.text())
        s["NIR_lambda"] = str(self.ui.tCCDNIRwavelength.text())
        s["FELP"] = str(self.ui.tCCDFELP.text())
        s["FELRR"] = str(self.ui.tCCDFELRR.text())
        s["FEL_lambda"] = str(self.ui.tCCDFELFreq.text())
        s["Sample_Temp"] = str(self.ui.tCCDSampleTemp.text())
        s["FEL_pulses"] = int(self.ui.tOscPulses.text())

        # If the user has the series box as {<variable>} where variable is
        # any of the keys below, we want to replace it with the relavent value
        # Potentially unnecessary at this point...
        st = str(self.ui.tCCDSeries.text())
        # NIRP, NIRW, FELF, FELP, SLITS
        st = st.format(NIRP=s["NIRP"], NIRW=s["NIR_lambda"], FELF=s["FEL_lambda"],
                       FELP=s["FELP"], SLITS=s["slits"], SPECL = s["center_lambda"])
        s["series"] = st
        return s

    def stopTimer(self, timer):
        """
        :param timer: timer to stop
        :return: None
        Timers are  obnoxious and can't be closed in the thread they weren't started in.
        This will allow you to emit a signal to stop the timer
        """
        timer.stop()

    def updateImage(self, isSig = True, isClean = False):
        if isSig:
            if isClean:
                self.pSigImage.setImage(self.curDataEMCCD.clean_array)
                self.pSigHist.setLevels(self.curDataEMCCD.clean_array.min(),
                                        self.curDataEMCCD.clean_array.max())
                try:
                    self.pSpec.setData(self.curDataEMCCD.spectrum[:,0],
                                   self.curDataEMCCD.spectrum[:,1])
                except Exception as e:
                    print 'Failed setting plot', e
            else:
                self.pSigImage.setImage(self.curData)
                self.pSigHist.setLevels(self.curData.min(), self.curData.max())
        else:
            if isClean:
                self.pBackImage.setImage(self.curBGEMCCD.clean_array)
                self.pBackHist.setLevels(self.curBGEMCCD.clean_array.min(),
                                        self.curBGEMCCD.clean_array.max())
            else:
                self.pBackImage.setImage(self.curBG)
                self.pBackHist.setLevels(self.curBG.min(), self.curBG.max())

    def updateProgress(self):
        if self.settings["progress"] < 100:
            self.settings["progress"] += 1
            self.ui.pCCD.setValue(self.settings["progress"])
            newTime = ((self.settings["progress"] + 1) * self.CCD.cameraSettings["exposureTime"]*10) \
                      - (self.elapsedTimer.elapsed())
            try:
                QtCore.QTimer.singleShot(newTime,
                                         self.updateProgress)
            except:
                pass
        else:
            self.updateElementSig.emit(self.ui.lCCDProg, "Reading Data")
            self.settings["exposing"] = False
            self.elapsedTimer = None

    def updateUIElement(self, element, val):
        """
        :param element: handle to UI element to update
        :param val: value to set to
        :return: None

        If I want to update a QLineEdit from within a thread, need to conncet it
        to a signal; main thread doesn't like to get update from outside itself
        """
        element.setText(str(val))
        
    def closeEvent(self, event):
        print 'closing,', event.type()
        try:
            print "Stopping temp timer"
            self.getTempTimer.stop()
        except:
            print "No timer to stop"
            pass
        try:
            print "Waiting for temperature set thread"
            self.setTempThread.wait()
        except:
            print "No temperature thread to wait for"
            pass

        try:
            print "Waiting for image collection to finish"
            self.getImageThread.wait()
        except:
            print "No image being collected."

        # if the detector is cooled, need to warm it back up
        try:
            if self.setTempThread.isRunning():
                print "Please wait for detector to warm"
                return
        except:
            pass
        if self.CCD.temperature<0:
            print 'Need to warm up the detector'

            self.dump = ChillerBox(self, "Please wait for detector to warm up")
            self.dump.show()

            # Set up a timer to destroy the window after some time.
            # Really, letting python garbage collecting take care of it
#            QtCore.QTimer.singleShot(3000, lambda: setattr(self, "dump", None))
            self.ui.tSettingsGotoTemp.setText('20')
            self.killFast = True
            self.doTempSet(0)
            try:
                self.setTempThread.finished.connect(self.dump.close)
            except Exception as e:
                print "Couldn't connect thread to closing,", e
            event.ignore()
            return


        #########
        # All clear, start closing things down
        #########

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
        self.Agilent.write(':RUN')

        ret = self.CCD.dllCoolerOFF()
        print "cooler off ret: {}".format(self.CCD.parseRetCode(ret))
        ret = self.CCD.dllShutDown()
        print "shutdown ret: {}".format(self.CCD.parseRetCode(ret))
        self.Spectrometer.close()

        self.CCD.cameraSettings = dict()  # Something is throwing an error when this isn't here
                                        # I think a memory leak somewhere?
        self.CCD.dll = None
        self.CCD = None


        self.close()

class ChillerBox(QtGui.QDialog):
    def __init__(self, parent=None, message = ""):
        super(ChillerBox, self).__init__(parent)
        self.message = message
        self.setupUi(self)

    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setEnabled(False)
        Dialog.resize(238, 42)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setWindowOpacity(53.0)
        self.horizontalLayout = QtGui.QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtGui.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(18)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Notice", None))
        self.label.setText(_translate("Dialog", self.message, None))

# Stuff for the dialog
_encoding = QtGui.QApplication.UnicodeUTF8
def _translate(context, text, disambig):
    return QtGui.QApplication.translate(context, text, disambig, _encoding)

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    ex = CCDWindow()
    sys.exit(app.exec_())



























































