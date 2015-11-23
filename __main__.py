# -*- coding: utf-8 -*-
"""
Created on Sat Feb 14 15:06:30 2015

@author: Home
"""

from __future__ import absolute_import

from Andor import AndorEMCCD
import pyqtgraph.console as pgc
from InstsAndQt.Instruments import *
from InstsAndQt.customQt import *
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

from UIs.mainWindow_ui import Ui_MainWindow
from ExpWidgs import *
from OscWid import *


try:
    a = QtCore.QString()
except AttributeError:
    QtCore.QString = str

neLines = [
    607.433, 609.616, 612.884, 614.306,
    616.359, 621.728, 626.649, 633.442,
    638.299, 640.225, 650.653, 653.288,
    659.895, 667.828, 671.704, 692.947,
    703.241, 717.394, 724.512, 743.890,
    747.244, 748.887, 753.577, 754.404
]


# class MessageDialog(object):
#     def __init__(self, *args, **kwargs):
#         pass


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
        if self.CCD.dllInitializeRet is not None:
            MessageDialog(self,
                          """Error! CCD was not initialized!
                          A fake camera was initialized!\n\n Error: {}""".format(
                              self.CCD.parseRetCode(self.CCD.dllInitializeRet)
                          ),
                          0)

        self.initUI()
        if self.checkSaveFile():
            self.loadOldSettings()

        # A note on the cooler:
        # This command will make it so the cooling fan
        # will not turn off when the software is closed.
        # Turning it off is bad when the temperature is <0
        # because it can lead to warming of the CCD chip at
        # damagingly fast rates. The option to leave it on
        # continuously has two main benefits
        # 1) If the software crashes (rare, but possible),
        #    the chip should stay cold and the software
        #    or SOLIS software can be started and recover
        #    safely
        # 2) Software changes that need to occur live, but
        #    after cooling, can be pushed after the CCD is
        #    cold without waiting 20 minutes for it to warm
        #    and recool
        #
        # For reason 1) above, we want to disable the auto-
        # shutoff of the cooler immediately to prevent issues
        # for software crashes.

        self.CCD.dllSetCoolerMode(1)

        # Check to make sure the software didn't crash and the temperature is currently cold
        temp = self.CCD.getTemperature()
        self.ui.tSettingsCurrTemp.setText(str(temp))
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
            # my mac claims to have this port,
            # cheap fix so it won't try to connect it
            if os.name == "posix":
                raise ValueError()
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
        # flag for allowing the automatic spectrometer sweeping
        s["doSpecSweep"] = False

        # Misc settings concerning the experimental parameters.
        # They are set by the children experimental widgets, but kept here so that
        # they can communicate with each other.

        s["nir_power"] = 0
        s["nir_lambda"] = 0
        s["nir_pol"] = 'H'
        s["series"] = ""
        s["sample_name"] = ""
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
        s["fel_pol"] = 'H'

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


        actionToWidgets = [(self.ui.fExpTypeAbs, AbsWid),
                           (self.ui.fExpTypeAlignment, AlignWid),
                           (self.ui.fExpTypeHSG_FVB, HSGFVBWid),
                           (self.ui.fExpTypeHSG_Image, HSGImageWid),
                           (self.ui.fExpTypeHSG_PhotonCounting, HSGPCWid),
                           (self.ui.fExpTypePL, PLWid),
                           (self.ui.fExpTypeTwo_Color_Abs, TwoColorAbsWid)
                           ]

        # Keep track of the qactions to iterate over
        # when changing experiments
        self.expMenuActions = []

        # Create all the widgets and store them in a dict
        # Keys are the qactions, because those are the
        # things that will trigger the changes
        for act, wid in actionToWidgets:
            self.expUIs[act] = wid(self)
            self.expUIs[act].setParent(None)
            self.expMenuActions.append(act)

        # Connect the changes
        [i.toggled[bool].connect(self.updateExperiment) for i in self.expMenuActions]

        self.oscWidget = None
        self.curExp = None # Keep a reference if you ever want it
        self.openExp([i for i in self.expMenuActions if i.isChecked()][0])


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
        # Later note:
        # I think I learned to just check the state of the UI element instead
        # of this dict value, but I'm not 100% sure
        self.ui.mFileDoCRR.triggered[bool].connect(lambda v: self.settings.__setitem__('doCRR', v))
        self.ui.mFileBreakTemp.triggered.connect(lambda: self.setTempThread.terminate())
        self.ui.mFileTakeContinuous.triggered[bool].connect(lambda v: self.getCurExp().startContinuous(v))
        self.ui.mFileEnableAll.triggered[bool].connect(self.toggleExtraSettings)
        self.ui.mFIleAbortAcquisition.triggered.connect(lambda v: self.getCurExp().abortAcquisition())

        ##
        # todo: follow through the removal of undo series
        # 11/6/15 undo series should be removed
        ##
        # self.ui.mSeriesUndo.triggered.connect(lambda x: self.getCurExp().undoSeries())
        # self.ui.mRemoveImageSequence.triggered.connect(lambda x: self.getCurExp().removeCurrentSeries())
        self.ui.mRemoveImageSequence.triggered.connect(
            lambda x: self.getCurExp().removeImageSequence()
        )

        self.ui.mRemoveBackgroundSequence.triggered.connect(
            lambda x: self.getCurExp().removeBackgroundSequence()
        )

        ##
        # todo: I'm not sure setting the current series is neccesary anymore
        # 11/6/15
        ##
        # self.ui.mSeriesReset.triggered.connect(lambda x: self.getCurExp().setCurrentSeries())



        self.ui.mLivePlotsForceAutoscale.triggered.connect(lambda x: self.getCurExp().autoscaleSignalHistogram())

        self.ui.mFileFastExit.triggered.connect(self.close)

        # self.sweep = self.ui.menuOther_Settings.addAction("Do Spec Sweep")
        self.sweep = self.ui.mFileDoSpecSweep
        self.sweep.setCheckable(True)
        self.sweep.triggered.connect(self.startSweepLoop)
        self.sweep.setEnabled(False)

        # self.neCal = self.ui.menuOther_Settings.addAction("Scan all Ne lines")
        self.neCal = self.ui.mFileScanNeLines
        self.neCal.triggered.connect(lambda : self.startSweepLoop(neLines))
        self.neCal.setEnabled(False)

        self.ui.mFileOpenDebugConsole.triggered.connect(self.openDebugConsole)

        

        ###############################
        #
        # These are commands for adding the motor controller
        # window.
        #
        ###########################
        self.addPolarizerMotorDriver()
        self.ui.miscToolsLayout.addStretch(10)


        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.show()

    @staticmethod
    def _________________________PE(): pass
    @staticmethod
    def CHANGING_EXPERIMENT_TYPE(): pass
    @staticmethod
    def __________________________pe(): pass
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
        expActions = self.expMenuActions
        [i.toggled.disconnect() for i in self.expMenuActions]
        # Keep track so we can close it.
        oldExp = [i for i in expActions if i is not sent and i.isChecked()][0]
        oldExp.setChecked(False)
        [i.toggled[bool].connect(self.updateExperiment) for i in self.expMenuActions]

        # Get the currently open tab to reopen it after they get
        # jumbled from closing things
        curTabIdx = self.ui.tabWidget.currentIndex()
        # Don't want to be closing/opening the scope if the new
        # experiment also uses it
        openScope = self.expUIs[sent].hasFEL and not self.expUIs[oldExp].hasFEL
        closeScope = not self.expUIs[sent].hasFEL and self.expUIs[oldExp].hasFEL
        self.closeExp(oldExp, closeScope = closeScope)

        self.openExp(sent, openScope = openScope)

        self.ui.tabWidget.setCurrentIndex(curTabIdx)

    def openExp(self, exp = "HSG", openScope = None):
        self.expUIs[exp].setParent(self)
        self.ui.tabWidget.insertTab(1, self.expUIs[exp], self.expUIs[exp].name)
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
        self.curExp.ui.tSampleName.setText(str(self.settings["sample_name"]))

        if self.curExp.hasNIR:
            self.curExp.ui.tCCDNIRwavelength.setText(str(self.settings["nir_lambda"]))
            self.curExp.ui.tCCDNIRP.setText(str(self.settings["nir_power"]))
            self.curExp.ui.tCCDNIRPol.setText(str(self.settings["nir_pol"]))
        if self.curExp.hasFEL:
            self.curExp.ui.tCCDFELP.setText(str(self.settings["fel_power"]))
            self.curExp.ui.tCCDFELFreq.setText(str(self.settings["fel_lambda"]))
            self.curExp.ui.tCCDFELRR.setText(str(self.settings["fel_reprate"]))
            self.curExp.ui.tCCDSpotSize.setText(str(self.settings["sample_spot_size"]))
            self.curExp.ui.tCCDWindowTransmission.setText(str(self.settings["window_trans"]))
            self.curExp.ui.tCCDEffectiveField.setText(str(self.settings["eff_field"]))
            self.curExp.ui.tCCDFELPol.setText(self.settings["fel_pol"])
        if openScope is None:
            openScope = self.expUIs[exp].hasFEL
        if openScope:
            self.openFELEquipment() # Opens up the oscilloscope

        self.curExp.experimentOpen()



    def closeExp(self, exp = "HSG", closeScope = None):
        self.curExp.experimentClose()
        self.ui.tabWidget.removeTab(
            self.ui.tabWidget.indexOf(self.expUIs[exp])
        )
        self.expUIs[exp].setParent(None)
        if closeScope is None:
            closeScope = self.curExp.hasFEL
        if closeScope:
            self.closeFELEquipment()
        self.curExp = None

    def openFELEquipment(self):
        self.oscWidget = OscWid(self)
        self.ui.tabWidget.insertTab(2, self.oscWidget, "Oscilloscope")

    def closeFELEquipment(self):
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
    def ____________ES(): pass
    @staticmethod
    def UI_CHANGES(): pass
    @staticmethod
    def ____________es(): pass


    def toggleExtraSettings(self, val=False):
        self.ui.cSettingsReadMode.setEnabled(val)
        self.ui.cSettingsAcquisitionMode.setEnabled(val)
        self.ui.cSettingsShutter.setEnabled(val)
        self.ui.tVBin.setEnabled(val)
        self.ui.tHBin.setEnabled(val)
        self.ui.tHStart.setEnabled(val)
        self.ui.tHEnd.setEnabled(val)
        self.sweep.setEnabled(val)
        self.neCal.setEnabled(val)

    def openDebugConsole(self):
        self.consoleWindow = pgc.ConsoleWidget(namespace={"self": self, "np": np})
        self.consoleWindow.show()


    def focusInEvent(self, event):
        if self.oscWidget is not None:
            if self.oscWidget.poppedPlotWindow is not None:
                self.oscWidget.poppedPlotWindow.raise_()
                self.raise_()


    def makeSpectraFolder(self):
        try:
            self.saveSettings()
        except:
            pass
        specFold = os.path.join(self.settings["saveDir"],
                                'Spectra', str(self.ui.tImageName.text()))
        if not os.path.exists(specFold):
            try:
                os.mkdir(specFold)
            except Exception as e:
                log.warning("Could not make folder for spectrum {}. Error: {}".format(specFold, e))

    def resetUICameraSettings(self):
        """
        This function is called when the UI needs to reflect
        whatever is specified in the CCD.cameraSettings dict. Two
        big reasons are
        1) User specifies invalid setting, want to reset it to
           whatever the camera actually has set.
        2) Want to automatically set the camera settings (recover from
           crash/shutdown). This call should be followed by
           self.updateSettings (with appropriate modification to
           self.settings['changedSettingsFlag']
        :return:
        """
        cBoxes = zip([self.ui.cSettingsADChannel,
                      self.ui.cSettingsVSS,
                      self.ui.cSettingsReadMode,
                      self.ui.cSettingsHSS,
                      self.ui.cSettingsTrigger,
                      self.ui.cSettingsAcquisitionMode,
                      self.ui.cSettingsShutter,
                      self.ui.cSettingsShutterEx],
                     ['curADChannel',
                      'curVSS',
                      'curReadMode',
                      'curHSS',
                      'curTrig',
                      'curAcqMode',
                      'curShutterInt',
                      'curShutterEx',
                      ])
        for uiElem, key in cBoxes:
            uiElem.setCurrentIndex(
                uiElem.findText(
                    str(self.CCD.cameraSettings[key])
                )
            )

        tBoxes = zip([self.ui.tHBin,
                      self.ui.tVBin,
                      self.ui.tHStart,
                      self.ui.tHEnd,
                      self.ui.tVStart,
                      self.ui.tVEnd],
                     self.CCD.cameraSettings['imageSettings'])

        for uiElem, key in tBoxes:
            uiElem.setText(str(key))
        self.settings["changedSettingsFlags"] = [0] * \
                                                len(self.settings["changedSettingsFlags"])
        self.ui.bSettingsApply.setEnabled(False)





    @staticmethod
    def _____________________GS(): pass

    @staticmethod
    def CHANGING_SETTINGS(): pass

    @staticmethod
    def _____________________gs(): pass

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
                self.warnSettingsFailure("AD Channel: {}".format(self.CCD.parseRetCode(ret)))
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
            if ret != 20002:
                log.error("Error updating VSS. Return code, {}".format(ret))
                self.warnSettingsFailure("VSS: {}".format(self.CCD.parseRetCode(ret)))
                return
            log.info('Change VSS: {}'.format(self.CCD.parseRetCode(ret)))
            self.settings["changedSettingsFlags"][1] = 0


        # Read mode has changed
        if changed[2] == 1:
            ret = self.CCD.setRead(self.ui.cSettingsReadMode.currentIndex())
            if ret != 20002:
                log.error("Error updating ReadMode. Return code, {}".format(ret))
                self.warnSettingsFailure("ReadMode: {}".format(self.CCD.parseRetCode(ret)))
                return
            log.info("Changed Read mode: {}".format(self.CCD.parseRetCode(ret)))
            self.settings["changedSettingsFlags"][2] = 0

        # HSS Changed
        if changed[3] == 1:
            ret = self.CCD.setHSS(self.ui.cSettingsHSS.currentIndex())
            if ret != 20002:
                log.error("Error updating HSS. Return code, {}".format(ret))
                self.warnSettingsFailure("HSS: {}".format(self.CCD.parseRetCode(ret)))
                return
            log.info("Changed HSS: {}".format(self.CCD.parseRetCode(ret)))
            self.settings["changedSettingsFlags"][3] = 0

        # Trigger mode changed
        if changed[4] == 1:
            ret = self.CCD.setTrigger(self.ui.cSettingsTrigger.currentIndex())
            if ret != 20002:
                log.error("Error updating Trigger. Return code, {}".format(ret))
                self.warnSettingsFailure("Trigger: {}".format(self.CCD.parseRetCode(ret)))
                return
            log.info('Changed Trigger: {}'.format(self.CCD.parseRetCode(ret)))
            self.settings["changedSettingsFlags"][4] = 0

        # changed Acquisition mode
        if changed[5] == 1:
            ret = self.CCD.setAcqMode(self.ui.cSettingsAcquisitionMode.currentIndex())
            if ret != 20002:
                log.error("Error updating Acq Mode. Return code, {}".format(ret))
                self.warnSettingsFailure("Acq Mode: {}".format(self.CCD.parseRetCode(ret)))
                return
            log.info('Changed Acq: {}'.format(self.CCD.parseRetCode(ret)))
            self.settings["changedSettingsFlags"][5] = 0

        # Did either of the shutter values changed
        if 1 in changed[6:8]:
            ret = self.CCD.setShutterEx(
                self.ui.cSettingsShutter.currentIndex(),
                self.ui.cSettingsShutterEx.currentIndex()
            )
            if ret != 20002:
                log.error("Error updating Shutter. Return code, {}".format(ret))
                self.warnSettingsFailure("Shutter: {}".format(self.CCD.parseRetCode(ret)))
                return
            log.info('Changed shutter: {}'.format(self.CCD.parseRetCode(ret)))
            self.settings["changedSettingsFlags"][6:8] = [0, 0]


        # Now change the settings parameters
        if 1 in self.settings["changedImageFlags"]:
            # Get the array to change to
            vals = [int(i.text()) for i in self.settings["imageUI"]]
            ret = self.CCD.setImage(vals)
            if ret != 20002:
                log.error("Error updating Image. Return code, {}".format(ret))
                self.warnSettingsFailure("Image: {}".format(self.CCD.parseRetCode(ret)))
                return
            log.info("Changed image: {}".format(self.CCD.parseRetCode(ret)))
            self.settings["changedImageFlags"] = [0, 0, 0, 0, 0, 0]

        self.ui.bSettingsApply.setEnabled(False)
        self.saveSettings()

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

    def warnSettingsFailure(self, extraInfo = None):
        """
        For when you choose to update the camera settings,
        but they get kicked back
        """
        msg = """ Error: Invalid parameters sent to camera
                      settings"""
        if isinstance(extraInfo, str):
            msg += extraInfo
        MessageDialog(self,
                      msg,
                      0)
        self.resetUICameraSettings()


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

    @staticmethod
    def _____________________LS(): pass
    @staticmethod
    def ADDING_MISC_TOOLS():pass
    @staticmethod
    def _____________________ls(): pass
    def addPolarizerMotorDriver(self):
        try:
            import motordriver.__main__ as md
        except ImportError:
            MessageDialog(self, "Error importing module for motor driver")
            return
        motorDriverGB = QtGui.QGroupBox("Attenuator", self)
        motorDriverGB.setFlat(True)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(md.MotorWindow())
        motorDriverGB.setLayout(layout)
        self.ui.miscToolsLayout.addWidget(motorDriverGB)

        # Disable the control panel for the motor driver
        # It the mutexs still occasionally lock if you're not careful,
        # and that could be catastrophic if the CCD is at -90 and
        # the software locks.
        #
        # Why am I doing it this way instead of keeping a reference
        # when instantiating, referencing it by that?
        #
        # Because this gives me a way to access it, without keeping
        # another class attribute, while the software is running
        # (If this or other objects need to be modified)
        # It is not pretty, and I apologize. It probably
        # wouldn't be hard to keep an internal reference,
        # but I don't see why; it shouldn't have to be referenced
        # after this point
        self.ui.miscToolsLayout.itemAt(0).widget().children()[1].ui.mMoreSettings.setEnabled(False)
        #                              |                      |_____[0] is the layout, [1] is the obj
        #                              |
        #                              |_______________________motordriver groupbox is the first thing in the layout

        self.ui.miscToolsLayout.itemAt(0).widget().children()[1].ui.bQuit.setEnabled(False)
    @staticmethod
    def _______________ER(): pass
    @staticmethod
    def SPECTROMETER(): pass
    @staticmethod
    def ________________er(): pass
    def SpecGPIBChanged(self):
        self.Spectrometer.close()
        self.settings["specGPIBidx"] = int(self.ui.cSpecGPIB.currentIndex())
        self.openSpectrometer()

    def openSpectrometer(self):
        # THIS should really be in a try:except: loop for if
        # the spec timeouts or cant be connected to
        try:
            # raise Exception("Cut this shit out, OSX. STOP OPENING IT")
            self.Spectrometer = ActonSP(
                self.settings["GPIBlist"][self.settings["specGPIBidx"]]
            )
        except Exception as e:
            log.warning("Could not initialize Spectrometer. GPIB: {}. Error{}".format(
                self.settings["GPIBlist"][self.settings["specGPIBidx"]], e))
            self.settings["specGPIBidx"] = self.ui.cSpecGPIB.findText('Fake')
            self.ui.cSpecGPIB.currentIndexChanged.disconnect(self.SpecGPIBChanged)
            self.ui.cSpecGPIB.setCurrentIndex(
                self.settings["specGPIBidx"]
            )
            self.ui.cSpecGPIB.currentIndexChanged.connect(self.SpecGPIBChanged)
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
        if hasattr(val, '__iter__'):
            # If you pass a list of values, just go to those
            # I want this for a lazy way to set the spectrometer to
            # Ne lines, too

            a = QtGui.QMessageBox()
            a.setText("Do you want to scan up?")
            a.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel)
            ret = a.exec_()
            if ret == QtGui.QMessageBox.Cancel:
                self.settings["doSpecSweep"] = False
                return
            elif ret == QtGui.QMessageBox.Yes:
                self.sweepRange = np.array(val)
            else:
                self.sweepRange = np.array(val)[::-1]

            self.thDoSpectrometerSweep.target = self.sweepLoop
            self.thDoSpectrometerSweep.start()
            self.settings["doSpecSweep"] = True
            return
        if val:
            start, step, end, ok = ScanParameterDialog.getSteps(self)
            if not ok:
                self.sweep.setChecked(False)
                self.settings["doSpecSweep"] = False
                return
            else:
                self.settings["doSpecSweep"] = True
                log.debug("Dialog accepted, {}, {}, {}".format(start, step, end))

                self.sweepRange = np.arange(start, end, step)
                self.thDoSpectrometerSweep.target = self.sweepLoop
                self.thDoSpectrometerSweep.start()
        else:
            self.settings["doSpecSweep"] = False # just getting turned off

    def sweepLoop(self):
        # Don't want it to keep asking if we want to save the image,
        # so redefine the checking function to always return true
        # Keep a reference to the old function so we can reset it
        # afterwards
        oldConfirmation = self.curExp.confirmImage
        self.curExp.confirmImage = lambda : True
        for wavelength in self.sweepRange:
            if not self.settings["doSpecSweep"]: break
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
            if not self.settings["doSpecSweep"]: break

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
        self.updateElementSig.emit(lambda : self.sweep.setChecked(False), None)
        log.debug("Done with scan")






    @staticmethod
    def ________________LS(): pass
    @staticmethod
    def CCD_CONTROLS(): pass
    @staticmethod
    def ________________ls(): pass

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


    @staticmethod
    def ____________NG(): pass
    @staticmethod
    def STATE_SAVING(): pass
    @staticmethod
    def ____________ng(): pass

    def saveSettings(self):
        """
        Sometimes software crashes or needs to be restarted,
        and all settings get lost. Sometimes this is just
        inconvenient, other times it can lead to potentially
        significant changes (pyro integration region change
        may change power). This function should be called
        when a parameter of interest gets changed, so
        the save file gets updated
        :return:
        """
        saveDict = dict()

        saveDict.update(self.settings)
        saveDict.update(self.CCD.cameraSettings)

        # These ones aren't needed and may be
        # bad to keep around.

        badKeys = ("settingsUI",
                   "GPIBlist",
                   "imageUI",
                   "takeContinuous",
                   "shouldScopeLoop",
                   "settingsUI",
                   "doSpecSweep",
                   "exposing",
                   "settingsUI",
        )

        for key in badKeys:
            try:
                del saveDict[key]
            except KeyError:
                pass
        saveDict['saveNameBG'] = str(self.ui.tBackgroundName.text())
        saveDict['saveName'] = str(self.ui.tImageName.text())
        saveDict['crr'] = bool(self.ui.mFileDoCRR.isChecked())
        saveDict['curExp'] = [str(ii.text()) for ii in self.expMenuActions if ii.isChecked()][0]

        # print "saving curvss", saveDict["curVSS"]
        with open('Settings.txt', 'w') as fh:
            json.dump(saveDict, fh, separators=(',', ': '),
                      sort_keys=True, indent=4, default=lambda x: 'NotSerial')

    @staticmethod
    def checkSaveFile():
        """
        This will check to see wheteher there's a previous settings file,
        and if it's recent enough that it should be loaded
        :return:
        """
        if not os.path.isfile('Settings.txt'):
            # File doesn't exist
            return False
        if (time.time() - os.path.getmtime('Settings.txt')) > 5 * 60:
            # It's been longer than 5 minutes and likely isn't worth
            # keeping open
            return False
        return True


    def loadOldSettings(self):
        """
        load old settings from the file.
        Note: this is pretty bad right now. It doesn't
        really handle the AD/HSS very well (especially
        because the AD set method is rather poor)
        But we don't change that very often, so
        for now, it'll just do it poorly.

        Also note: I think things could go rather badly
        if something goes wrong when setting:
        If we force a change to the software CCDsettings dict,
        but something fails when we try to set it, the software
        will still "think" it's at whatever we force here,
        even though it may not be.

        However, this hopefully shouldn't be an issue. These
        settings that we force should be whatever were last used,
        and I can't imagine how the real deal camera would haev
        a setting disappear.
        :return:
        """

        with open('Settings.txt') as fh:
            savedDict = json.load(fh)
        self.settings.update({k:v for k,v in savedDict.items() if k in self.settings})

        expose = savedDict.pop('exposureTime')
        gain = savedDict.pop('gain')


        self.CCD.cameraSettings.update(
            {k:v for k,v in savedDict.items() if k in self.CCD.cameraSettings})

        # Call to set all of the camera settings to what we've loaded
        self.resetUICameraSettings()


        self.settings["changedSettingsFlags"] = [1] * \
                                                len(self.settings["changedSettingsFlags"])
        self.settings["changedImageFlags"] = [1] * \
                                                len(self.settings["changedImageFlags"])
        # Force a camera update
        self.updateSettings()

        # reopen the experiment tab, which should
        # repopulate the experimental parameters.
        # Might be a better way of doing this, but fekkit
        curExp = self.getCurExp()
        curExpAct = [k for k,v in self.expUIs.items() if v is curExp][0]
        self.closeExp(curExpAct)

        [i.toggled.disconnect() for i in self.expMenuActions]
        [ii.setChecked(False) for ii in self.expMenuActions]
        curExpAct = [ ii for ii in self.expMenuActions if str(ii.text()) == savedDict.get('curExp', self.expMenuActions[0])][0]
        curExpAct.setChecked(True)
        [i.toggled[bool].connect(self.updateExperiment) for i in self.expMenuActions]

        self.openExp(curExpAct)
        self.getCurExp().ui.tEMCCDExp.setText(str(expose))
        self.getCurExp().ui.tEMCCDGain.setText(str(gain))

        self.ui.tSettingsDirectory.setText(str(self.settings["saveDir"]))
        self.ui.tImageName.setText(str(savedDict['saveName']))
        self.ui.tBackgroundName.setText(str(savedDict['saveNameBG']))
        self.ui.mFileDoCRR.setChecked(savedDict['crr'])



    @staticmethod
    def ___________CS(): pass
    @staticmethod
    def MISC_FUNCS(): pass
    @staticmethod
    def ___________cs(): pass

    def stopTimer(self, timer):
        """
        :param timer: timer to stop
        :return: None
        Timers are  obnoxious and can't be closed in the thread they weren't started in.
        This will allow you to emit a signal to stop the timer
        """
        timer.stop()

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
        self.saveSettings()
        print 'closing,', event.type()

        fastExit = False
        if self.sender() == self.ui.mFileFastExit:
            ret = QtGui.QMessageBox.warning(
                self,
                "Warning",
                "This will leave the CCD and cooler on.\n"
                "Only use if you intend to immediately restart "
                "control software",
                QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel,
                QtGui.QMessageBox.Cancel
            )
            if ret == QtGui.QMessageBox.Cancel:
                event.ignore()
                return
            fastExit = True
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

        # Make sure the shutter isn't accidentally left open
        # 0,0 -> Auto
        self.CCD.setShutterEx(0, 0)
        if self.ui.tabWidget.indexOf(self.oscWidget) is not -1:
            self.oscWidget.close()
        if not fastExit:
            ret = self.CCD.dllCoolerOFF()
            log.debug("cooler off ret: {}".format(self.CCD.parseRetCode(ret)))
            ret = self.CCD.dllSetCoolerMode(0)
            log.debug("coller off ret: {}".format(self.CCD.parseRetCode(ret)))
            # ret = self.CCD.dllShutDown()
            # log.debug("shutdown ret: {}".format(self.CCD.parseRetCode(ret)))
        else:
            log.warning("Didn't turn off the cooler!")
        ret = self.CCD.dllShutDown()
        log.debug("shutdown ret: {}".format(self.CCD.parseRetCode(ret)))
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



























































