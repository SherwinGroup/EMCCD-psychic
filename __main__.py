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
from image_spec_for_gui import EMCCD_image
import copy
from Instruments import *

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


class CCDWindow(QtGui.QMainWindow):
    # signal definitions
    updateElementSig = QtCore.pyqtSignal(object, object) # This can be used for updating any element
    killTimerSig = QtCore.pyqtSignal(object) # To kill a timer started in the main thread from a sub-thread
     # to update either image, whether it is clean or not
    updateDataSig = QtCore.pyqtSignal(object, object)

    # Thread definitions
    setTempThread = None
    getTempTimer = None # Timer for updating the current temperature while the detector is warming/cooling

    getImageThread = None
    updateProgTimer = None # timer for updating the progress bar

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

        self.updateElementSig.connect(self.updateUIElement)
        self.killTimerSig.connect(self.stopTimer)
        self.updateDataSig.connect(self.updateImage)

    def initSettings(self):
        s = dict() # A dictionary to keep track of miscellaneous settings

        # Get the GPIB instrument list
        try:
            import visa
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

        # Which settings combo boxes have been changed?
        # AD, VSS, Read, HSS, Trigg, Acq
        s["changedSettingsFlags"] = [0, 0, 0, 0, 0, 0]

        # Which image boxes have been changed?
        # HBin, VBin, HSt, HEn, VSt, VEn
        s["changedImageFlags"] = [0, 0, 0, 0, 0, 0] # Flags for when we change the
                                                                # image settings.
        s["settingsUI"] = None # Keep track of the settings comboboxes for iteration
        s["imageUI"] = None # keep ttrack of the settings param textedits for iteration
        s["isImage"] = True # Is it an image read mode?

        s["bgSaveDir"] = '' # Save dirs
        s["imSaveDir"] = ''

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

        ####################
        # Create a list of the ui setting handles for iteration
        ###################
        self.settings["settingsUI"] = [self.ui.cSettingsADChannel,
                                       self.ui.cSettingsVSS,
                                       self.ui.cSettingsReadMode,
                                       self.ui.cSettingsHSS,
                                       self.ui.cSettingsTrigger,
                                       self.ui.cSettingsAcquisitionMode]

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
        self.ui.bSettingsBGDirectory.clicked.connect(self.chooseSaveDir)
        self.ui.tSettingsBGDirectory.setEnabled(False)
        self.ui.bSettingsIMGDirectory.clicked.connect(self.chooseSaveDir)
        self.ui.tSettingsIMGDirectory.setEnabled(False)

        ##################
        # Connections for updating image counters when user-changed
        ##################
        self.ui.tCCDImageNum.textAccepted.connect(
            lambda: self.updateImageNumbers(True))
        self.ui.tCCDBGNum.textAccepted.connect(
            lambda: self.updateImageNumbers(False))

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

        self.pSpec = self.ui.gCCDBin.plot()
        plotitem = self.ui.gCCDBin.getPlotItem()
        plotitem.setLabel('top',text='Spectrum')
        plotitem.setLabel('left',text='Wavelength',units='nm')
        plotitem.setLabel('bottom',text='Counts')

        self.show()

    def SpecGPIBChanged(self):
        self.Spectrometer.close()
        self.settings["specGPIBidx"] = int(self.ui.cSpecGPIB.currentIndex())
        self.openSpectrometer()

    def openSpectrometer(self):
        self.Spectrometer = ActonSP(
            self.settings["GPIBlist"][self.settings["specGPIBidx"]]
        )
        self.ui.tSpecCurWl.setText(str(self.Spectrometer.getWavelength()))
        self.ui.tSpecCurGr.setText(str(self.Spectrometer.getGrating()))

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

        for (i, uiEle) in enumerate(self.settings["imageUI"]):
            uiEle.setText(str(self.CCD.cameraSettings['imageSettings'][i]))

    def chooseSaveDir(self):
        sent = self.sender()

        if sent == self.ui.bSettingsBGDirectory:
            hint = "Choose Background Directory"
            prevDir = self.settings["bgSaveDir"]
        else:
            hint = "Choose Image Directory"
            prevDir = self.settings["imSaveDir"]
        file = str(QtGui.QFileDialog.getExistingDirectory(self, hint, prevDir))
        if file == '':
            return
        #Update the appropriate file
        if sent == self.ui.bSettingsBGDirectory:
            self.settings["bgSaveDir"] = file
            self.ui.tSettingsBGDirectory.setText(file)
        else:
            self.settings["imSaveDir"] = file
            self.ui.tSettingsIMGDirectory.setText(file)

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

    def cleanupSetTemp(self):
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
        self.settings["progress"] = 0
        self.getImageThread = TempThread(target = self.takeImage, args=imtype)

        # Update exposure/gain if necesssary
        if not np.isclose(float(self.ui.tEMCCDExp.text()), self.CCD.cameraSettings["exposureTime"]):
            self.CCD.setExposure(float(self.ui.tEMCCDExp.text()))
        if not int(self.ui.tEMCCDGain.text()) == self.CCD.cameraSettings["gain"]:
            self.CCD.setGain(int(self.ui.tEMCCDGain.text()))

        self.updateProgTimer = QtCore.QTimer()
        self.updateProgTimer.timeout.connect(self.updateProgress)
        self.updateProgTimer.start(self.CCD.cameraSettings["exposureTime"]*10)

        self.getImageThread.start()

    def takeImage(self, imtype):

        self.updateElementSig.emit(self.ui.lCCDProg, "Waiting exposure")

        self.CCD.dllStartAcquisition()
        self.CCD.dllWaitForAcquisition()
        self.killTimerSig.emit(self.updateProgTimer)
        self.updateElementSig.emit(self.ui.lCCDProg, "Reading Data")

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
                                            str(self.ui.tImageName.text())+str(self.ui.tCCDImageNum.text()),
                                            str(self.ui.tCCDComments.toPlainText()),
                                            self.genEquipmentDict())
            try:
                self.curDataEMCCD.save_images(self.settings["imSaveDir"])
            except Exception as e:
                print "Error saving data image", e
            try:
                self.curDataEMCCD.cosmic_ray_removal()
            except Exception as e:
                print "cosmic,",e
            try:
                self.curDataEMCCD = self.curDataEMCCD - self.curBGEMCCD
            except Exception as e:
                print e

            try:
                self.curDataEMCCD.make_spectrum()
            except Exception as e:
                print e
            try:
                self.curDataEMCCD.save_spectrum(self.settings["imSaveDir"])
            except Exception as e:
                print "Error saving spectrum,",e
            self.updateDataSig.emit(True, True) # update with the cleaned data
        else:
            self.curBGEMCCD = EMCCD_image(self.curBG,
                                            str(self.ui.tBackgroundName.text())+str(self.ui.tCCDBGNum.text()),
                                            str(self.ui.tCCDComments.toPlainText()),
                                            self.genEquipmentDict())
            try:
                self.curBGEMCCD.save_images(self.settings["bgSaveDir"])
            except Exception as e:
                print "Error saving background iamge", e
            self.curBGEMCCD.cosmic_ray_removal()
            self.curBGEMCCD.make_spectrum()
            self.updateDataSig.emit(False, True) # update with the cleaned data

        self.updateElementSig.emit(self.ui.lCCDProg, "Done.")
        self.ui.bCCDImage.setEnabled(True)
        self.ui.bCCDBack.setEnabled(True)

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
        s["grating"] = int(self.ui.tSpecCurGr.text())
        s["center_lambda"] = float(self.ui.tSpecCurWl.text())
        s["slits"] = str(self.ui.tCCDSlits.text())
        s["dark_region"] = None
        s["bg_file_name"] = str(self.ui.tBackgroundName.text()) + str(self.ui.tCCDBGNum.text())
        s["NIRP"] = str(self.ui.tCCDNIRP.text())
        s["NIR_lambda"] = str(self.ui.tCCDNIRwavelength.text())
        s["FELP"] = str(self.ui.tCCDFELP.text())
        s["FELRR"] = str(self.ui.tCCDFELRR.text())
        s["FEL_lambda"] = str(self.ui.tCCDFELFreq.text())

        st = str(self.ui.tCCDSeries.text())
        # NIRP, NIRW, FELF, FELP, SLITS
        st = st.format(NIRP=s["NIRP"], NIRW=s["NIR_lambda"], FELF=s["FEL_lambda"],
                       FELP=s["FELP"], SLITS=s["slits"])
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
        self.settings["progress"] += 1
        self.ui.pCCD.setValue(self.settings["progress"])

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
            QtCore.QTimer.singleShot(3000, lambda: setattr(self, "dump", None))
            self.ui.tSettingsGotoTemp.setText('20')
            self.killFast = True
            self.doTempSet(0)
            try:
                self.setTempThread.finished.connect(self.dump.close())
            except:
                print "Couldn't connect thread to closing"
            event.ignore()
            return

        ret = self.CCD.dllCoolerOFF()
        print "ooler off ret: {}".format(self.CCD.parseRetCode(ret))
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



























































