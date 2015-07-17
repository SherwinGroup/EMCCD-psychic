# -*- coding: utf-8 -*-
"""
Created on Sat Feb 14 15:06:30 2015

@author: Home
"""

import numpy as np
from PyQt4 import QtCore, QtGui
from Andor import AndorEMCCD
import pyqtgraph as pg
import pyqtgraph.console as pgc
import scipy.integrate as spi
from image_spec_for_gui import EMCCD_image, calc_THz_intensity, calc_THz_field
from InstsAndQt.Instruments import *
from InstsAndQt.customQt import *
import copy
import os
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
try:
    import visa
except:
    log.critical('GPIB VISA library not installed')
    raise

import logging



log = logging.getLogger("EMCCD")
log.setLevel(logging.DEBUG)
handler = logging.FileHandler("TheLog.log")
handler.setLevel(logging.DEBUG)
handler1 = logging.StreamHandler()
handler1.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - [%(filename)s:%(lineno)s - %(funcName)s()] - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
handler1.setFormatter(formatter)
log.addHandler(handler)
log.addHandler(handler1)

# http://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105#1552105
import ctypes
if os.name is not "posix":
    myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

# http://stackoverflow.com/questions/279237/import-a-module-from-a-relative-path?lq=1
# import os, sys, inspect
# cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"UIs")))
# if cmd_subfolder not in sys.path:
#      sys.path.insert(0, cmd_subfolder)
from UIs.mainWindow_ui import Ui_MainWindow
from ExpWidgs import *
from OscWid import *

try:
    a = QtCore.QString()
except AttributeError:
    QtCore.QString = str


class CCDWindow(QtGui.QMainWindow):
    # signal definitions
    updateElementSig = QtCore.pyqtSignal(object, object) # This can be used for updating any element
    killTimerSig = QtCore.pyqtSignal(object) # To kill a timer started in the main thread from a sub-thread
     # to update either image, whether it is clean or not
    updateDataSig = QtCore.pyqtSignal(object, object, object)

    # Thread definitions
    setTempThread = None
    getTempTimer = None # Timer for updating the current temperature while the detector is warming/cooling

    sigUpdateStatusBar = QtCore.pyqtSignal(object)

    # Should be moved to ExpWid's
    getImageThread = None
    updateProgTimer = None # timer for updating the progress bar
    getContinuousThread = None # Thread for acquiring continuously
    updateOscDataSig = QtCore.pyqtSignal()

    thDoSpectrometerSweep = TempThread()


    def __init__(self):
        super(CCDWindow, self).__init__()
        log.debug("About to initialize settins")
        self.initSettings()
        # instantiate the CCD class so that we can get values from it to
        # populate menus in the UI.
        try:
            self.CCD = AndorEMCCD(wantFake = False)
        except TypeError as e:
            log.critical("Could not instantiate camera class, {}".format(e))
            self.close()

        self.CCD.initialize()

        self.initUI()

        # Check to make sure the software didn't crash and the temperature is currently cold
        temp = self.CCD.getTemperature()
        self.ui.tSettingsGotoTemp.setText(str(temp))
        if temp < 0:
            self.doTempSet(temp)

        self.Spectrometer = None
        self.Agilent = None
        self.openSpectrometer()
        # self.openAgilent()
        self.poppedPlotWindow = None

        self.updateElementSig.connect(self.updateUIElement)
        self.killTimerSig.connect(self.stopTimer)


    def initSettings(self):
        s = dict() # A dictionary to keep track of miscellaneous settings

        # Get the GPIB instrument list
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
            # ASRL1
            idx = s['GPIBlist'].index('ASRL1::INSTR')
            s["specGPIBidx"] = idx
        except ValueError:
            # otherwise, just set it to the fake index
            s["specGPIBidx"] = s['GPIBlist'].index('Fake')
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


        # list of the field intensities for each pulse in a scan
        s["fieldStrength"] = []
        s["fieldInt"] = []
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
        s["seriesNo"] = 0 # How many series have been summed together?

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

        # Past things for series stuff
        self.prevDataEMCCD = None
        self.prevBGEMCCD = None

        # The current value contaiend in the progress bar
        s["progress"] = 0
        self.killFast = False

        # do you want me to remove cosmic rays?
        s["doCRR"] = True
        s["takeContinuous"] = False

        # Misc settings concerning the experimental parameters.
        # They are set by the children experimental widgets, but kept here so that
        # they can communicate with each other.

        s["nir_power"] = 0
        s["nir_lambda"] = 0
        s["series"] = ""
        s["fel_power"] = 0
        s["exposure"] = 0.5
        s["gain"] = 1
        s["y_min"] = 0
        s["y_max"] = 400
        s["slits"] = 0
        s["fel_reprate"] = 0.75
        s["fel_lambda"] = 0
        s["sample_temp"] = 0
        s["fel_pulses"] = 0
        s["sample_spot_size"] = 0.05
        s["window_trans"] = 1.0
        s["eff_field"] = 1.0

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



        self.sbText = QTimedText()
        self.statusBar().addPermanentWidget(self.sbText, 1)
        self.sigUpdateStatusBar.connect(self.updateStatusBar)

        #####################
        # Creating all of the widgets used for different experiment types
        ###################
        self.expUIs = dict()
        self.expUIs["HSG"] = HSGWid(self)
        self.expUIs["HSG"].setParent(None)
        self.expUIs["Abs"] = AbsWid(self)
        self.expUIs["Abs"].setParent(None)
        self.expUIs["PL"] = PLWid(self)
        self.expUIs["PL"].setParent(None)
        self.expUIs["Two Color Abs"] = TwoColorAbsWid(self)
        self.expUIs["Two Color Abs"].setParent(None)
        # Connect the changes
        [i.toggled[bool].connect(self.updateExperiment) for i in self.ui.menuExperiment_Type.actions()]

        self.oscWidget = None
        self.curExp = None # Keep a reference if you ever want it
        # self.openHSG()
        self.openExp("HSG")


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
        # Connect all of the setting changes for the CCD parameters
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


                                    
        ####################
        # Connect more things
        ###################
        self.ui.cSettingsVSS.setCurrentIndex(1)
        self.ui.bSettingsApply.setEnabled(False)
        self.ui.bSettingsApply.clicked.connect(self.updateSettings)
        self.ui.bSettingsCancel.clicked.connect(self.cancelSettings)
        self.ui.bSetTemp.clicked.connect(self.doTempSet)

        ####################
        # Save file connection
        ##################
        self.ui.bSettingsDirectory.clicked.connect(self.chooseSaveDir)
        self.ui.tSettingsDirectory.setEnabled(False)

        ##################
        # Connections for file menu things
        ##################
        # All I want it to do is set a flag which gets checked later.
        self.ui.mFileDoCRR.triggered[bool].connect(lambda v: self.settings.__setitem__('doCRR', v))
        self.ui.mFileBreakTemp.triggered.connect(lambda: self.setTempThread.terminate())
        self.ui.mFileTakeContinuous.triggered[bool].connect(lambda v: self.getCurExp().startContinuous(v))
        self.ui.mFileEnableAll.triggered[bool].connect(self.toggleExtraSettings)
        # self.ui.mSeriesUndo.triggered.connect(self.undoLastSeries)
        self.ui.mSeriesUndo.triggered.connect(self.getCurExp().undoSeries)
        self.ui.mFileFastExit.triggered.connect(self.close)

        self.sweep = self.ui.menuOther_Settings.addAction("Do Spec Sweep")
        self.sweep.setCheckable(True)
        self.sweep.triggered.connect(self.startSweepLoop)
        self.sweep.setEnabled(False)

        self.console = self.ui.menuOther_Settings.addAction("Open Debug Console")
        self.console.triggered.connect(self.openDebugConsole)


        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.show()

    @staticmethod
    def __CHANGING_EXPERIMENT_TYPE(): pass
    def updateExperiment(self, b):
        sent = self.sender()
        if not b: # You unchecked it, which isn't advised
            sent.toggled.disconnect()
            sent.setChecked(True)
            sent.toggled[bool].connect(self.updateExperiment)
            return
        # ensure en exposure isn't taking place
        if self.curExp.thDoExposure.isRunning():
            sent.toggled.disconnect()
            sent.setChecked(False)
            sent.toggled[bool].connect(self.updateExperiment)
            self.sigUpdateStatusBar.emit("Please wait for image to collect")
            return



        #disconnect the actions, change to the proper toggle, and reconenct them
        expActions = self.ui.menuExperiment_Type.actions()
        [i.toggled.disconnect() for i in self.ui.menuExperiment_Type.actions()]
        # Keep track so we can close it.
        oldExp = str([i for i in expActions if i is not sent and i.isChecked()][0].text())
        [i.setChecked(False) for i in expActions if i is not sent]
        [i.toggled[bool].connect(self.updateExperiment) for i in self.ui.menuExperiment_Type.actions()]

        curTabIdx = self.ui.tabWidget.currentIndex()
        newExp = str(sent.text())
        # if oldExp == "HSG":
        #     self.closeHSG()
        if oldExp in ["HSG", "PL", "Abs", "Two Color Abs"]:
            # hasFEL = self.getCurExp().hasFEL
            self.closeExp(oldExp)
            # if hasFEL:
            #     self.closeHSG()
        else:
            log.error("Unknown old experiment, {}".format(oldExp))

        # if newExp == "HSG":
        #     self.openHSG()
        if newExp in ["HSG", "PL", "Abs", "Two Color Abs"]:
            self.openExp(newExp)
            # if self.getCurExp().hasFEL:
            #     self.openHSG()
        else:
            log.error("Unknown experiment chosen, {}".format(newExp))


        self.ui.tabWidget.setCurrentIndex(curTabIdx)

    def openExp(self, exp = "HSG"):
        self.expUIs[exp].setParent(self)
        self.ui.tabWidget.insertTab(1, self.expUIs[exp], exp)
        self.curExp = self.expUIs[exp]

        # Need to set the texts so that they're constant between them all.
        self.curExp.ui.tCCDImageNum.setText(str(self.settings["igNumber"]))
        self.curExp.ui.tCCDBGNum.setText(str(self.settings["bgNumber"]))
        self.curExp.ui.tCCDSeries.setText(str(self.settings["series"]))
        self.curExp.ui.tEMCCDExp.setText(str(self.CCD.cameraSettings["exposureTime"]))
        self.curExp.ui.tEMCCDGain.setText(str(self.CCD.cameraSettings["gain"]))
        self.curExp.ui.tCCDSampleTemp.setText(str(self.settings["sample_temp"]))
        self.curExp.ui.tCCDYMin.setText(str(self.settings["y_min"]))
        self.curExp.ui.tCCDYMax.setText(str(self.settings["y_max"]))
        self.curExp.ui.tCCDSlits.setText(str(self.settings["slits"]))

        if self.curExp.hasNIR:
            self.curExp.ui.tCCDNIRwavelength.setText(str(self.settings["nir_lambda"]))
            self.curExp.ui.tCCDNIRP.setText(str(self.settings["nir_power"]))
        if self.curExp.hasFEL:
            self.curExp.ui.tCCDFELP.setText(str(self.settings["fel_power"]))
            self.curExp.ui.tCCDFELFreq.setText(str(self.settings["fel_lambda"]))
            self.curExp.ui.tCCDFELRR.setText(str(self.settings["fel_reprate"]))
            self.curExp.ui.tCCDSpotSize.setText(str(self.settings["sample_spot_size"]))
            self.curExp.ui.tCCDWindowTransmission.setText(str(self.settings["window_trans"]))
            self.curExp.ui.tCCDEffectiveField.setText(str(self.settings["eff_field"]))
            self.openHSG() # Opens up the oscilloscope



    def closeExp(self, exp = "HSG"):
        self.ui.tabWidget.removeTab(
            self.ui.tabWidget.indexOf(self.expUIs[exp])
        )
        self.expUIs[exp].setParent(None)
        if self.curExp.hasFEL:
            self.closeHSG()
        self.curExp = None

    def openHSG(self):
        self.oscWidget = OscWid(self)
        self.ui.tabWidget.addTab(self.oscWidget, "Oscilloscope")

    def closeHSG(self):
        self.ui.tabWidget.removeTab(
            self.ui.tabWidget.indexOf(self.oscWidget)
        )
        self.oscWidget.close()
        self.oscWidget = None

    def getCurExp(self):
        # I need this function for an easy fix
        # I want to connect a signal/slot at initialization
        # but that corresponds to the curExp at that time,
        # not at all times
        return self.curExp

    @staticmethod
    def __UI_CHANGES(): pass


    def toggleExtraSettings(self, val=False):
        self.ui.cSettingsReadMode.setEnabled(val)
        self.ui.cSettingsAcquisitionMode.setEnabled(val)
        self.ui.cSettingsShutter.setEnabled(val)
        self.ui.tVBin.setEnabled(val)
        self.ui.tHBin.setEnabled(val)
        self.ui.tHStart.setEnabled(val)
        self.ui.tHEnd.setEnabled(val)
        self.sweep.setEnabled(val)

    def openDebugConsole(self):
        self.consoleWindow = pgc.ConsoleWidget(namespace={"self": self, "np": np})
        self.consoleWindow.show()


    def focusInEvent(self, event):
        if self.oscWidget is not None:
            if self.oscWidget.poppedPlotWindow is not None:
                self.oscWidget.poppedPlotWindow.raise_()
                self.raise_()


    def parseImageChange(self, st):
        """
        Called when the image settings are changed.
        :param st: value changed to
        :return:
        """
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
            log.info('Change AD Channel: {}'.format(self.CCD.parseRetCode(ret)))
            if ret != 20002:
                log.error("Error updating AD Channel. Return code, {}".format(ret))
                return

            # Changing the AD changes the available HSS. Find out what they are,
            # update the list of choices. Then change HSS to the first value
            self.CCD.getHSS()
            self.ui.cSettingsHSS.clear()
            self.ui.cSettingsHSS.addItems([str(i) for i in self.CCD.cameraSettings['HSS']])
            ret = self.CCD.setHSS(0)
            log.info('Change HSS, AD: {}'.format(self.CCD.parseRetCode(ret)))
            self.ui.cSettingsHSS.setCurrentIndex(0)

            # Unflag for change of AD
            self.settings["changedSettingsFlags"][0] = 0
            # Unflag change of HSS (we don't care what you previously wanted, it's likely not
            # there anymore.
            self.settings["changedSettingsFlags"][3] = 0

        # The VSS has changed
        if changed[1] == 1:
            ret = self.CCD.setVSS(int(self.ui.cSettingsVSS.currentIndex()))
            log.info('Change VSS: {}'.format(self.CCD.parseRetCode(ret)))
            self.settings["changedSettingsFlags"][1] = 0


        # Read mode has changed
        if changed[2] == 1:
            ret = self.CCD.setRead(self.ui.cSettingsReadMode.currentIndex())
            log.info("Changed Read mode: {}".format(self.CCD.parseRetCode(ret)))
            self.settings["changedSettingsFlags"][2] = 0

        # HSS Changed
        if changed[3] == 1:
            ret = self.CCD.setHSS(self.ui.cSettingsHSS.currentIndex())
            log.info("Changed HSS: {}".format(self.CCD.parseRetCode(ret)))
            self.settings["changedSettingsFlags"][3] = 0

        # Trigger mode changed
        if changed[4] == 1:
            ret = self.CCD.setTrigger(self.ui.cSettingsTrigger.currentIndex())
            log.info('Changed Trigger: {}'.format(self.CCD.parseRetCode(ret)))
            self.settings["changedSettingsFlags"][4] = 0

        # changed Acquisition mode
        if changed[5] == 1:
            ret = self.CCD.setAcqMode(self.ui.cSettingsAcquisitionMode.currentIndex())
            log.info('Changed Acq: {}'.format(self.CCD.parseRetCode(ret)))
            self.settings["changedSettingsFlags"][5] = 0

        # Did either of the shutter values changed
        if 1 in changed[6:8]:
            ret = self.CCD.setShutterEx(
                self.ui.cSettingsShutter.currentIndex(),
                self.ui.cSettingsShutterEx.currentIndex()
            )
            log.info('Changed shutter: {}'.format(self.CCD.parseRetCode(ret)))
            self.settings["changedSettingsFlags"][6:8] = [0, 0]


        # Now change the settings parameters
        if 1 in self.settings["changedImageFlags"]:
            # Get the array to change to
            vals = [int(i.text()) for i in self.settings["imageUI"]]
            ret = self.CCD.setImage(vals)
            log.info("Changed image: {}".format(self.CCD.parseRetCode(ret)))
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
        log.debug("filename: {}".format(filen))
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
                log.warning("Failed creating new image directory, {}".format(newIm))

        if not os.path.exists(newSpec):
            try:
                os.mkdir(newSpec)
            except:
                log.warning("Failed creating new spectra directory, {}".format(newSpec))

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
                log.warning("Could not make folder for spectrum {}. Error: {}".format(specFold, e))

    @staticmethod
    def __SPECTROMETER(): pass
    def SpecGPIBChanged(self):
        self.Spectrometer.close()
        self.settings["specGPIBidx"] = int(self.ui.cSpecGPIB.currentIndex())
        self.openSpectrometer()

    def openSpectrometer(self):
        # THIS should really be in a try:except: loop for if
        # the spec timeouts or cant be connected to
        try:
            self.Spectrometer = ActonSP(
                self.settings["GPIBlist"][self.settings["specGPIBidx"]]
            )
        except Exception as e:
            log.warning("Could not initialize Spectrometer. GPIB: {}. Error{}".format(
                self.settings["GPIBlist"][self.settings["specGPIBidx"]], e))
            self.Spectrometer = ActonSP("Fake")
        try:
            self.ui.tSpecCurWl.setText(str(self.Spectrometer.getWavelength()))
            self.ui.sbSpecWavelength.setValue(self.Spectrometer.getWavelength())
            self.ui.tSpecCurGr.setText(str(self.Spectrometer.getGrating()))
            self.ui.sbSpecGrating.setValue(self.Spectrometer.getWavelength())
        except Exception as e:
            log.warning("Could not get spectrometer values, {}".format(e))

    def updateSpecWavelength(self):
        desired = float(self.ui.sbSpecWavelength.value())
        new = self.Spectrometer.goAndAsk(desired, doCal = True)
        self.ui.tSpecCurWl.setText(str(new))

    def updateSpecGrating(self):
        desired = int(self.ui.sbSpecGrating.value())
        self.Spectrometer.setGrating(desired)
        new = self.Spectrometer.getGrating()
        self.ui.tSpecCurGr.setText(str(new))

    def startSweepLoop(self, val):
        if val:
            start, step, end, ok = ScanParameterDialog.getSteps(self)
            if not ok:
                self.sweep.setChecked(False)
                return
            else:
                log.debug("Dialog accepted, {}, {}, {}".format(start, step, end))

                self.sweepRange = np.arange(start, end, step)
                self.thDoSpectrometerSweep.target = self.sweepLoop
                self.thDoSpectrometerSweep.start()
        else: pass # just getting turned off (heh)

    def sweepLoop(self):
        # Don't want it to keep asking if we want to save the image,
        # so redefine the checking function to always return true
        # Keep a reference to the old function so we can reset it
        # afterwards
        oldConfirmation = self.curExp.confirmImage
        self.curExp.confirmImage = lambda : True
        for wavelength in self.sweepRange:
            if not self.sweep.isChecked(): break
            log.debug("At wavelength {}".format(wavelength))
            self.updateElementSig.emit(lambda: self.ui.sbSpecWavelength.setValue(wavelength), None)
            time.sleep(0.5) # need to make sure the spectrometer and all things
                            # get updated before startinge verything else
                            # do it before calling update, so taht those
                            # timing issues with signals are avoided
            self.updateSpecWavelength()
            self.sigUpdateStatusBar.emit(str(wavelength))
            self.ui.cSettingsShutterEx.setCurrentIndex(2) # perm closed
            self.settings["changedSettingsFlags"][-1] = 1
            self.updateSettings()
            log.debug("set shutter closed")

            self.curExp.ui.bCCDBack.clicked.emit(False) # emulate button press for laziness
            log.debug("Called Take bacground")
            time.sleep(0.5)
            self.curExp.thDoExposure.wait()

            self.ui.cSettingsShutterEx.setCurrentIndex(0) # auto
            self.settings["changedSettingsFlags"][-1] = 1
            self.updateSettings()
            log.debug("set shutter Auto")
            if not self.sweep.isChecked(): break

            self.curExp.ui.bCCDImage.clicked.emit(False) # emulate button press for laziness
            log.debug("Called Take image")

            time.sleep(0.5)
            self.curExp.thDoExposure.wait()

            # When analyzing, it would be nice to have origin
            # import the data with the y-data labeled by
            # the center lambda for ease with the legends/labeling
            # Also add the file number foreasier identification
            self.curExp.curDataEMCCD.origin_import = '\nWavelength,{}-{}\nnm,nm'.format(
                self.curExp.curDataEMCCD.equipment_dict["center_lambda"],
                self.curExp.curDataEMCCD.file_no
            )
            try:
                self.curExp.curDataEMCCD.save_spectrum(self.settings["saveDir"])
            except Exception as e:
                log.debug("Error saving durings spectrum sweep {}".format(e))
        self.curExp.confirmImage = oldConfirmation
        log.debug("Done with scan")







    @staticmethod
    def __CCD_CONTROLS(): pass

    def undoLastSeries(self):
        log.warning("UNDO LAST SERIES NOT IMPLEMENTED")

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
        if temp is None or type(temp) is bool: # bool test is because buttons send a value if clicked, want to ignore
            temp = int(self.ui.tSettingsGotoTemp.text())
        log.debug("Going to temperature: {}".format(temp))

        # Disable the buttons we don't want messed with
        # self.ui.bCCDBack.setEnabled(False)
        # self.ui.bCCDImage.setEnabled(False)
        # self.ui.bSetTemp.setEnabled(False)
        [i.toggleUIElements(False) for i in self.expUIs.values()]

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
        # self.ui.bCCDImage.setEnabled(True)
        # self.ui.bCCDBack.setEnabled(True)
        # self.ui.bSetTemp.setEnabled(True)
        [i.toggleUIElements(True) for i in self.expUIs.values()]
        self.getTempTimer.stop()

        self.updateTemp()

    def updateTemp(self):
        self.ui.tSettingsCurrTemp.setText(str(self.CCD.temperature))
        self.ui.tSettingsTempResponse.setText(self.CCD.tempRetCode)

    # def startTakeImage(self, imtype = "img"):
    #     self.ui.bCCDImage.setEnabled(False)
    #     self.ui.bCCDBack.setEnabled(False)
    #     self.ui.gbSettings.setEnabled(False)
    #     # Reset all the things kept track of during an exposure
    #     self.settings["progress"] = 0
    #     self.settings["FELPulses"] = 0
    #     self.settings["fieldStrength"] = []
    #     self.settings["fieldInt"] = []
    #     self.ui.tOscPulses.setText("0")
    #     self.getImageThread = TempThread(target = self.takeImage, args=imtype)
    #
    #     # Update exposure/gain if necesssary
    #     if not np.isclose(float(self.ui.tEMCCDExp.text()), self.CCD.cameraSettings["exposureTime"]):
    #         self.CCD.setExposure(float(self.ui.tEMCCDExp.text()))
    #     if not int(self.ui.tEMCCDGain.text()) == self.CCD.cameraSettings["gain"]:
    #         self.CCD.setGain(int(self.ui.tEMCCDGain.text()))
    #
    #     # self.updateProgTimer = QtCore.QTimer()
    #     # self.updateProgTimer.timeout.connect(self.updateProgress)
    #     # self.updateProgTimer.start(self.CCD.cameraSettings["exposureTime"]*10)
    #
    #     self.elapsedTimer = QtCore.QElapsedTimer()
    #     if self.settings["isScopePaused"]:
    #         self.settings["exposing"] = True
    #         self.elapsedTimer.start()
    #         QtCore.QTimer.singleShot(self.CCD.cameraSettings["exposureTime"]*10,
    #                                  self.updateProgress)
    #     else:
    #         self.updateOscDataSig.connect(self.startProgressBar)
    #     self.getImageThread.start()
    #
    # def startProgressBar(self):
    #     self.settings["exposing"] = True
    #     self.elapsedTimer.start()
    #     QtCore.QTimer.singleShot(self.CCD.cameraSettings["exposureTime"]*10,
    #                              self.updateProgress)
    #     # Don't want the signal to keep calling this functin
    #     self.updateOscDataSig.disconnect(self.startProgressBar)
    #
    #
    # def takeImage(self, imtype):
    #     """
    #     Want to have the exposing flags set here just so there's no funny business
    #     Sometimes the other thread may msibehave and we don't want photons to keep on
    #     counting
    #     """
    #     self.settings["exposing"] = True
    #     self.updateElementSig.emit(self.ui.lCCDProg, "Waiting exposure")
    #     self.CCD.dllStartAcquisition()
    #     self.CCD.dllWaitForAcquisition()
    #     self.settings["exposing"] = False
    #     # self.killTimerSig.emit(self.updateProgTimer)
    #     data = self.CCD.getImage()
    #
    #     # Store the data appropriately and update the graphe
    #     if imtype=="img":
    #         self.curData = data
    #         self.updateDataSig.emit(True, False, False)
    #     else:
    #         self.curBG = data
    #         self.updateDataSig.emit(False, False, False)
    #
    #     self.updateElementSig.emit(self.ui.lCCDProg, "Cleaning Data")
    #
    #     ####################################
    #     #
    #     # Concerning the image numbers:
    #     #
    #     # Things were getting confusing having an internal variable and the textbox
    #     # so switched to only using textbox. But this has issue that, since texboxes
    #     # can't be updated from non-main threads (or it's unpredictable), signals are needed
    #     # But this has issues that a fast computer will instantiate the object before
    #     # the text is updated, so they're out of sync. This way, we know that the textbox
    #     # will be incremented by one, but we forcibly tell it that it's going to be incremented
    #     # instead of hoping that things will time properly
    #     #
    #     ####################################
    #     if imtype=="img":
    #         self.curDataEMCCD = EMCCD_image(self.curData,
    #                                         str(self.ui.tImageName.text()),
    #                                         str(self.ui.tCCDImageNum.value()+1),
    #                                         str(self.ui.tCCDComments.toPlainText()),
    #                                         self.genEquipmentDict())
    #         self.updateElementSig.emit(self.ui.tCCDImageNum, self.ui.tCCDImageNum.value()+1)
    #         try:
    #             self.curDataEMCCD.save_images(self.settings["saveDir"])
    #         except Exception as e:
    #             log.warning("Error saving data image, {}".format(e))
    #
    #         if self.settings["doCRR"]:
    #             try:
    #                 self.curDataEMCCD.cosmic_ray_removal()
    #             except Exception as e:
    #                 print "cosmic,",e
    #         else:
    #             self.curDataEMCCD.clean_array = self.curDataEMCCD.raw_array
    #
    #         try:
    #             self.curDataEMCCD = self.curDataEMCCD - self.curBGEMCCD
    #         except Exception as e:
    #             print 'subraction:', e
    #
    #         try:
    #             self.curDataEMCCD.make_spectrum()
    #         except Exception as e:
    #             print e
    #
    #         try:
    #             self.curDataEMCCD.inspect_dark_regions()
    #         except Exception as e:
    #             print "Error inspecting dark region", e
    #
    #         try:
    #             self.curDataEMCCD.save_spectrum(self.settings["saveDir"])
    #         except Exception as e:
    #             log.warning("Error saving spectrum,",e)
    #         self.updateDataSig.emit(True, True, False) # update with the cleaned data
    #
    #
    #         #######################
    #         # Handling of series tag to add things up live
    #         #
    #         # Want it to save only the latest series, but also
    #         # the previous ones should be saved (hence why this is
    #         # after the saving is being done)
    #         #######################
    #         if (self.prevDataEMCCD is not None and
    #                     str(self.ui.tCCDSeries.text()) != "" and
    #                     self.prevDataEMCCD.equipment_dict["series"] ==
    #                     self.curDataEMCCD.equipment_dict["series"] and
    #                 self.ui.mSeriesSum.isChecked()):
    #             log.debug("Added to previous series")
    #             # Un-normalize by the number currently in series
    #             self.prevDataEMCCD.clean_array*=self.settings["seriesNo"]
    #             try:
    #                 self.prevDataEMCCD += self.curDataEMCCD
    #             except Exception as e:
    #                 log.warning("Error adding data in series: {}".format(e))
    #             # print "\n\tPOST: {}, {}".format(id(self.prevDataEMCCD))
    #             self.ui.mSeriesUndo.setEnabled(True)
    #
    #             self.prevDataEMCCD.make_spectrum()
    #
    #             # Save the summed, unnormalized spectrum
    #             try:
    #                 self.prevDataEMCCD.save_spectrum(self.settings["saveDir"])
    #             except Exception as e:
    #                 log.warning("Error saving SERIES spectrum, {}".format(e))
    #
    #             self.settings["seriesNo"] +=1
    #             self.ui.groupBox_42.setTitle("Series ({})".format(self.settings["seriesNo"]))
    #             # but PLOT the normalized average
    #             self.prevDataEMCCD.spectrum[:,1]/=self.settings["seriesNo"]
    #             self.prevDataEMCCD.clean_array/=self.settings["seriesNo"]
    #
    #             # Update the plots with this new data
    #             self.updateDataSig.emit(True, True, True)
    #
    #         elif str(self.ui.tCCDSeries.text()) != "" and self.ui.mSeriesSum.isChecked():
    #             log.info("Had to make a new series")
    #             self.prevDataEMCCD = copy.deepcopy(self.curDataEMCCD)
    #             self.prevDataEMCCD.file_no += "seriesed"
    #             self.settings["seriesNo"] = 1
    #             self.ui.groupBox_42.setTitle("Series (1)")
    #
    #
    #         else:
    #             #######################
    #             # THINK ABOUT HTIS WHEN YOU'RE NOT TIRED
    #             #######################
    #             self.prevDataEMCCD = None
    #             self.settings["seriesNo"] = 0
    #             self.ui.groupBox_42.setTitle("Series")
    #
    #     else:
    #         self.curBGEMCCD = EMCCD_image(self.curBG,
    #                                         str(self.ui.tBackgroundName.text()),
    #                                         str(self.ui.tCCDBGNum.value()+1),
    #                                         str(self.ui.tCCDComments.toPlainText()),
    #                                         self.genEquipmentDict())
    #         self.updateElementSig.emit(self.ui.tCCDBGNum, self.ui.tCCDBGNum.value()+1)
    #         try:
    #             self.curBGEMCCD.save_images(self.settings["saveDir"])
    #         except Exception as e:
    #             log.warning("Error saving background iamge, {}".format(e))
    #
    #         if self.settings["doCRR"]:
    #             self.curBGEMCCD.cosmic_ray_removal()
    #         else:
    #             self.curBGEMCCD.clean_array = self.curBGEMCCD.raw_array
    #
    #         self.curBGEMCCD.make_spectrum()
    #
    #         self.curBGEMCCD.inspect_dark_regions()
    #
    #         self.updateDataSig.emit(False, True, False) # update with the cleaned data
    #
    #     self.updateElementSig.emit(self.ui.lCCDProg, "Done.")
    #     self.ui.bCCDImage.setEnabled(True)
    #     self.ui.bCCDBack.setEnabled(True)
    #     self.ui.gbSettings.setEnabled(True)
    #
    # def startTakeContinuous(self, val):
    #     if val is True:
    #     # Update exposure/gain if necesssary
    #         if not np.isclose(float(self.ui.tEMCCDExp.text()), self.CCD.cameraSettings["exposureTime"]):
    #             self.CCD.setExposure(float(self.ui.tEMCCDExp.text()))
    #         if not int(self.ui.tEMCCDGain.text()) == self.CCD.cameraSettings["gain"]:
    #             self.CCD.setGain(int(self.ui.tEMCCDGain.text()))
    #         self.ui.gbSettings.setEnabled(False)
    #         self.ui.bCCDBack.setEnabled(False)
    #         self.ui.bCCDImage.setEnabled(False)
    #         self.p1.addItem(self.ilOne)
    #         self.p1.addItem(self.ilTwo)
    #         self.getContinuousThread = TempThread(target = self.takeContinuous)
    #         self.getContinuousThread.start()
    #
    # def takeContinuous(self):
    #     while self.ui.mFileTakeContinuous.isChecked():
    #         self.CCD.dllStartAcquisition()
    #         self.CCD.dllWaitForAcquisition()
    #         self.curData = self.CCD.getImage()
    #         self.updateDataSig.emit(True, False, False)
    #
    #     self.p1.removeItem(self.ilOne)
    #     self.p1.removeItem(self.ilTwo)
    #
    #     self.ui.gbSettings.setEnabled(True)
    #     self.ui.bCCDBack.setEnabled(True)
    #     self.ui.bCCDImage.setEnabled(True)
    #
    #
    # def genEquipmentDict(self):
    #     """
    #     The EMCCD class wants a specific dictionary of values. This function will return it
    #     :return:
    #     """
    #     s = dict()
    #     s["ccd_temperature"] = str(self.ui.tSettingsCurrTemp.text())
    #     s["exposure"] = float(self.CCD.cameraSettings["exposureTime"])
    #     s["gain"] = int(self.CCD.cameraSettings["gain"])
    #     s["y_min"] = int(self.ui.tCCDYMin.text())
    #     s["y_max"] = int(self.ui.tCCDYMax.text())
    #     s["grating"] = int(self.ui.sbSpecGrating.value())
    #     s["center_lambda"] = float(self.ui.sbSpecWavelength.value())
    #     s["slits"] = str(self.ui.tCCDSlits.text())
    #     s["dark_region"] = None
    #     s["bg_file_name"] = str(self.ui.tBackgroundName.text()) + str(self.ui.tCCDBGNum.value())
    #     s["nir_power"] = str(self.ui.tCCDNIRP.text())
    #     s["nir_lambda"] = str(self.ui.tCCDNIRwavelength.text())
    #     s["fel_power"] = str(self.ui.tCCDFELP.text())
    #     s["fel_reprate"] = str(self.ui.tCCDFELRR.text())
    #     s["fel_lambda"] = str(self.ui.tCCDFELFreq.text())
    #     s["sample_Temp"] = str(self.ui.tCCDSampleTemp.text())
    #     s["fel_pulses"] = int(self.ui.tOscPulses.text())
    #     s["fieldStrength"] = self.settings["fieldStrength"]
    #     s["fieldInt"] = self.settings["fieldInt"]
    #     s["number_of_series"] = self.settings["seriesNo"]
    #
    #     # If the user has the series box as {<variable>} where variable is
    #     # any of the keys below, we want to replace it with the relavent value
    #     # Potentially unnecessary at this point...
    #     st = str(self.ui.tCCDSeries.text())
    #     # NIRP, NIRW, FELF, FELP, SLITS
    #     st = st.format(NIRP=s["NIRP"], NIRW=s["NIR_lambda"], FELF=s["FEL_lambda"],
    #                    FELP=s["FELP"], SLITS=s["slits"], SPECL = s["center_lambda"])
    #     s["series"] = st
    #     return s

    def stopTimer(self, timer):
        """
        :param timer: timer to stop
        :return: None
        Timers are  obnoxious and can't be closed in the thread they weren't started in.
        This will allow you to emit a signal to stop the timer
        """
        timer.stop()

    # def updateImage(self, isSig = True, isClean = False, isSeries = False):
    #     """
    #     :param isSig: To update the top or bottom
    #     :param isClean: Where to get the updated data from (local thing or the
    #                     EMCCD class
    #     :param isSeries: A flag for whether we take from prevDataEMCCD or not
    #     :return:
    #     """
    #     if isSeries:
    #         log.debug("updated image from series data")
    #         self.pSpec.setData(self.prevDataEMCCD.spectrum[:,0],
    #                                self.prevDataEMCCD.spectrum[:,1])
    #         self.pSigImage.setImage(self.prevDataEMCCD.clean_array)
    #         self.pSigHist.setLevels(self.prevDataEMCCD.clean_array.min(),
    #                                 self.prevDataEMCCD.clean_array.max())
    #         return
    #
    #     if isSig:
    #         if isClean:
    #             self.pSigImage.setImage(self.curDataEMCCD.clean_array)
    #             self.pSigHist.setLevels(self.curDataEMCCD.clean_array.min(),
    #                                     self.curDataEMCCD.clean_array.max())
    #             try:
    #                 self.pSpec.setData(self.curDataEMCCD.spectrum[:,0],
    #                                self.curDataEMCCD.spectrum[:,1])
    #             except Exception as e:
    #                 log.debug('Failed setting plot', e)
    #         else:
    #             self.pSigImage.setImage(self.curData)
    #             self.pSigHist.setLevels(self.curData.min(), self.curData.max())
    #     else:
    #         if isClean:
    #             self.pBackImage.setImage(self.curBGEMCCD.clean_array)
    #             self.pBackHist.setLevels(self.curBGEMCCD.clean_array.min(),
    #                                     self.curBGEMCCD.clean_array.max())
    #         else:
    #             self.pBackImage.setImage(self.curBG)
    #             self.pBackHist.setLevels(self.curBG.min(), self.curBG.max())
    #
    # def undoLastSeries(self):
    #     log.debug("Substracting last data")
    #     # pg.plot(self.prevDataEMCCD.spectrum[:,0],
    #     #                            self.prevDataEMCCD.spectrum[:,1], title="pre")
    #     # Un-normalize by the number of FEL pulses
    #     self.prevDataEMCCD.clean_array *= self.settings["seriesNo"]
    #
    #     self.prevDataEMCCD -= self.curDataEMCCD
    #     self.settings["seriesNo"]-=1
    #     self.ui.groupBox_42.setTitle("Series ({})".format(self.settings["seriesNo"]))
    #
    #     self.prevDataEMCCD.make_spectrum()
    #     try:
    #         self.prevDataEMCCD.save_spectrum(self.settings["saveDir"])
    #     except Exception as e:
    #         log.warning("Error saving SERIES spectrum after undo, {}".format(e))
    #
    #     # renormalize by the number of pulses
    #     try:
    #         self.prevDataEMCCD.clean_array/=self.settings["seriesNo"]
    #     except ZeroDivisionError:
    #         pass
    #     try:
    #         self.prevDataEMCCD.spectrum[:,1]/=self.settings["seriesNo"]
    #     except:
    #         pass
    #
    #     self.updateDataSig.emit(True, True, True)
    #     self.ui.mSeriesUndo.setEnabled(False)
    #
    # def updateProgress(self):
    #     if self.settings["progress"] < 100:
    #         self.settings["progress"] += 1
    #         self.ui.pCCD.setValue(self.settings["progress"])
    #         newTime = ((self.settings["progress"] + 1) * self.CCD.cameraSettings["exposureTime"]*10) \
    #                   - (self.elapsedTimer.elapsed())
    #         if newTime < 0:
    #             newTime = 0
    #         try:
    #             QtCore.QTimer.singleShot(newTime,
    #                                      self.updateProgress)
    #         except:
    #             pass
    #     else:
    #         self.updateElementSig.emit(self.ui.lCCDProg, "Reading Data")
    #         self.settings["exposing"] = False
    #         self.elapsedTimer = None

    def updateUIElement(self, element, val):
        """
        :param element: handle to UI element to update
        :param val: value to set to
        :return: None

        If I want to update a QLineEdit from within a thread, need to conncet it
        to a signal; main thread doesn't like to get update from outside itself
        """

        # Sometimes you don't want to just setText, you want more.
        # In that case, let them jsut pass a lambda and this will call
        # it from the main thread, avoiding threading issues
        if hasattr(element, "__call__"):
            element()
            return

        element.setText(str(val))

    def updateStatusBar(self, obj):
        """

        :param obj: Either a string to print in the status bar or a list of [str, time (ms)]
        :return:
        """
        if type(obj) is str:
            self.sbText.setMessage(obj)
        elif type(obj) is list:
            self.sbText.setMessage(obj[0], [1])
        
    def closeEvent(self, event):
        print 'closing,', event.type()
        fastExit = False
        if self.sender() == self.ui.mFileFastExit:
            # Note, this does not work. Remove this stuff in a future version.
            pass
            # ret = QtGui.QMessageBox.warning(
            #     self,
            #     "Warning",
            #     "This will leave the CCD and cooler on.\n"
            #     "Only use if you intend to immediately restart "
            #     "control software",
            #     QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel,
            #     QtGui.QMessageBox.Cancel
            # )
            # if ret == QtGui.QMessageBox.Cancel:
            #     event.ignore()
            #     return
            # fastExit = True
        try:
            log.info("Waiting for temperature set thread")
            self.setTempThread.wait()
        except:
            log.info("No temperature thread to wait for")
            pass
        try:
            log.info("Stopping temp timer")
            self.getTempTimer.stop()
        except:
            log.info("No timer to stop")
            pass

        if self.ui.mFileTakeContinuous.isChecked():
            self.ui.mFileTakeContinuous.setChecked(False)
            try:
                self.curExp.thDoExposure.wait()
            except Exception as e:
                log.debug("Error waiting for continuous taking {}".format(e))

        try:
            log.info("Waiting for image collection to finish")
            self.curExp.thDoExposure.wait()
        except:
            log.info("No image being collected.")

        # if the detector is cooled, need to warm it back up
        try:
            if self.setTempThread.isRunning():
                log.info("Please wait for detector to warm")
                return
        except:
            pass
        temp = self.CCD.getTemperature()
        self.updateTemp()

        if temp<0 and not fastExit:
            log.info('Need to warm up the detector')

            self.dump = ChillerBox(self, "Please wait for detector to warm up")
            self.dump.show()

            self.ui.tSettingsGotoTemp.setText('20')
            self.killFast = True
            self.doTempSet(0)
            try:
                self.setTempThread.finished.connect(self.dump.close)
            except Exception as e:
                log.warning("Couldn't connect thread to closing popup, {}".format(e))
            event.ignore()
            return


        #########
        # All clear, start closing things down
        #########

        if self.ui.tabWidget.indexOf(self.oscWidget) is not -1:
            self.oscWidget.close()
        if not fastExit:
            ret = self.CCD.dllCoolerOFF()
            log.debug("cooler off ret: {}".format(self.CCD.parseRetCode(ret)))
            ret = self.CCD.dllShutDown()
            log.debug("shutdown ret: {}".format(self.CCD.parseRetCode(ret)))
        else:
            log.warning("Didn't shut down the CCD!")
        self.Spectrometer.close()

        self.CCD.cameraSettings = dict()  # Something is throwing an error when this isn't here
                                        # I think a memory leak somewhere?
        # self.CCD.dll = None
        # self.CCD = None
        del self.CCD.dll
        del self.CCD

        event.accept()
        self.close()

class ScanParameterDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(ScanParameterDialog, self).__init__(parent=parent)

        mainLayout = QtGui.QVBoxLayout(self)

        layout = QtGui.QHBoxLayout(self)

        start = QtGui.QGroupBox("Start")
        start.setFlat(True)
        startlayout = QtGui.QHBoxLayout(self)
        step = QtGui.QGroupBox("Step")
        step.setFlat(True)
        steplayout = QtGui.QHBoxLayout(self)
        stop = QtGui.QGroupBox("Stop")
        stop.setFlat(True)
        stoplayout = QtGui.QHBoxLayout(self)

        self.tStart = QFNumberEdit(self)
        self.tStart.setText("760")
        self.tStep = QFNumberEdit(self)
        self.tStep.setText("-1")
        self.tStop = QFNumberEdit(self)
        self.tStop.setText("740")

        startlayout.addWidget(self.tStart)
        steplayout.addWidget(self.tStep)
        stoplayout.addWidget(self.tStop)

        start.setLayout(startlayout)
        step.setLayout(steplayout)
        stop.setLayout(stoplayout)

        layout.addWidget(start)
        layout.addWidget(step)
        layout.addWidget(stop)

        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        mainLayout.addLayout(layout)
        mainLayout.addWidget(buttons)

        self.setLayout(mainLayout)


    @staticmethod
    def getSteps(parent = None):
        dialog = ScanParameterDialog(parent)
        result = dialog.exec_()

        return dialog.tStart.value(), dialog.tStep.value(), dialog.tStop.value(), result==QtGui.QDialog.Accepted


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



























































