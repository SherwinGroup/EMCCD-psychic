# -*- coding: utf-8 -*-
"""
Created on Sat Feb 14 15:06:30 2015

@author: Home
"""

import numpy as np
from PyQt4 import QtCore, QtGui
from mainWindow_ui import Ui_MainWindow
from Andor import AndorEMCCD
import threading
import time

try:
    import visa
except:
    print 'GPIB VISA library not installed'
    raise



class TempThread(QtCore.QThread):
    def __init__(self, target, args):
        super(TempThread, self).__init__()
        self.target = target
        self.args = args

    def run(self):
        self.target(self.args)


class CCDWindow(QtGui.QMainWindow):
    #signal definitions

    # Thread definitions
    setTempThread = None
    getTempTimer = None # Timer for updating the current temperature while the detector is warming/cooling

    def __init__(self):
        super(CCDWindow, self).__init__()
        self.initSettings()

        # instantiate the CCD class so that we can get values from it to
        # populate menus in the UI.
        self.CCD = AndorEMCCD()
        self.CCD.initialize()


        self.initUI()

    def initSettings(self):
        s = dict() # A dictionary to keep track of miscellaneous settings

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
            self.ui.cSettingsAcquisitionMode.model().setData(j, QtCore.QVariant(0), QtCore.Qt.UserRole-1)


        # Updating menus in the settings/CCD settings portion
        self.ui.cSettingsADChannel.addItems([str(i) for i in range(
            self.CCD.cameraSettings['numADChannels'])])
        self.ui.cSettingsVSS.addItems([str(i) for i in self.CCD.cameraSettings['VSS']])
        self.ui.cSettingsHSS.addItems([str(i) for i in self.CCD.cameraSettings['HSS']])
        self.ui.tHBin.setText(str(self.CCD.cameraSettings['imageSettings'][0]))
        self.ui.tVBin.setText(str(self.CCD.cameraSettings['imageSettings'][1]))
        self.ui.tHStart.setText(str(self.CCD.cameraSettings['imageSettings'][2]))
        self.ui.tHEnd.setText(str(self.CCD.cameraSettings['imageSettings'][3]))
        self.ui.tVStart.setText(str(self.CCD.cameraSettings['imageSettings'][4]))
        self.ui.tVEnd.setText(str(self.CCD.cameraSettings['imageSettings'][5]))


        self.ui.cSettingsReadMode.currentIndexChanged[QtCore.QString].connect(self.parseSettingsChange)
        self.ui.cSettingsADChannel.currentIndexChanged[QtCore.QString].connect(self.parseSettingsChange)
        self.ui.cSettingsVSS.currentIndexChanged[QtCore.QString].connect(self.parseSettingsChange)
        self.ui.cSettingsHSS.currentIndexChanged[QtCore.QString].connect(self.parseSettingsChange)
        self.ui.cSettingsTrigger.currentIndexChanged[QtCore.QString].connect(self.parseSettingsChange)
        self.ui.cSettingsAcquisitionMode.currentIndexChanged[QtCore.QString].connect(self.parseSettingsChange)
        self.settings["settingsUI"] = [self.ui.cSettingsADChannel,
                                       self.ui.cSettingsVSS,
                                       self.ui.cSettingsReadMode,
                                       self.ui.cSettingsHSS,
                                       self.ui.cSettingsTrigger,
                                       self.ui.cSettingsAcquisitionMode]

        self.ui.tHBin.textAccepted[object].connect(self.parseImageChange)
        self.ui.tHStart.textAccepted[object].connect(self.parseImageChange)
        self.ui.tHEnd.textAccepted[object].connect(self.parseImageChange)
        self.ui.tVBin.textAccepted[object].connect(self.parseImageChange)
        self.ui.tVStart.textAccepted[object].connect(self.parseImageChange)
        self.ui.tVEnd.textAccepted[object].connect(self.parseImageChange)
        self.settings["imageUI"] = [self.ui.tHBin,
                                    self.ui.tVBin,
                                    self.ui.tHStart,
                                    self.ui.tHEnd,
                                    self.ui.tVStart,
                                    self.ui.tVEnd]


        self.ui.bSettingsApply.setEnabled(False)

        self.ui.bSettingsApply.clicked.connect(self.updateSettings)
        self.ui.bSettingsCancel.clicked.connect(self.cancelSettings)


        self.ui.bSettingsBGDirectory.clicked.connect(self.chooseSaveDir)
        self.ui.tSettingsBGDirectory.setEnabled(False)
        self.ui.bSettingsIMGDirectory.clicked.connect(self.chooseSaveDir)
        self.ui.tSettingsIMGDirectory.setEnabled(False)

        self.ui.bSetTemp.clicked.connect(self.doTempSet)

        self.ui.bCCDImage.clicked.connect(self.takeImage)
        self.ui.bCCDBack.clicked.connect(self.takeBackground)

        self.pSigImage = self.ui.gCCDImage


        self.show()

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
            prevDir = self.settings["bgSaveDir"]
        file = str(QtGui.QFileDialog.getExistingDirectory(self, hint, prevDir))
        if file == '':
            return
        #Update the appropriate file
        if sent == self.ui.bSettingsBGDirectory:
            self.settings["bgSaveDir"] = file
            self.ui.tSettingsBGDirectory.setText(file)
        else:
            self.settings["bgSaveDir"] = file
            self.ui.tSettingsIMGDirectory.setText(file)

    def doTempSet(self, temp = None):
        # temp is so that it can be called during cleanup.
        if not self.settings['askedChiller']:
            self.settings['askedChiller'] = True
            self.dump = ChillerBox()
            self.dump.show()

            # Set up a timer to destroy the window after some time.
            # Really, letting python garbage collecting take care of it
            QtCore.QTimer.singleShot(3000, lambda: setattr(self, "dump", None))
        if temp is None:
            temp = int(self.ui.tSettingsGotoTemp.text())

        # Disable the buttons we don't want messed with
        self.ui.bCCDBack.setEnabled(False)
        self.ui.bCCDImage.setEnabled(False)
        self.ui.bSetTemp.setEnabled(False)

        # Set up a thread which will handle the monitoring of the temperature
        self.setTempThread = TempThread(target = self.CCD.gotoTemperature, args = temp)
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

    def takeImage(self):
        if not np.isclose(float(self.ui.tEMCCDExp.text()), self.CCD.cameraSettings["exposureTime"]):
            self.CCD.setExposure(float(self.ui.tEMCCDExp))
        if not int(self.ui.tEMCCDGain.text()) == self.CCD.cameraSettings["gain"]:
            self.CCD.setGain(int(self.ui.tEMCCDGain.text()))


        # Need to do a ccd.dllStartAcquisition and all that timing!


        self.curData = self.CCD.getImage()
        self.pSigImage.setImage(self.curData)




    def takeBackground(self):
        pass

    def closeEvent(self, event):
        print 'closing,', event.type()
        try:
            self.getTempTimer.stop()
        except:
            pass
        try:
            self.setTempThread.wait()
        except:
            pass

        # if the detector is cooled, need to warm it back up
        if self.CCD.temperature<0:
            if self.setTempThread.isRunning():
                print "Please wait for detector to warm"
                return
            print 'Need to warm up the detector'
            self.doTempSet(0)
            event.ignore()
            return

        self.CCD.dllCoolerOFF()
        self.CCD.dllShutDown()

        self.CCD.cameraSettings=dict()  # Something is throwing an error when this isn't here
                                        # I think a memory leak somewhere?
        self.CCD.dll = None
        self.CCD = None


        self.close()

class ChillerBox(QtGui.QDialog):
    def __init__(self, parent=None):
        super(ChillerBox, self).__init__(parent)
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
        Dialog.setWindowTitle(_translate("Dialog", "Turn On The Chiller", None))
        self.label.setText(_translate("Dialog", "Did you turn on the chiller?", None))

# Stuff for the dialog
_encoding = QtGui.QApplication.UnicodeUTF8
def _translate(context, text, disambig):
    return QtGui.QApplication.translate(context, text, disambig, _encoding)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.setEnabled(False)
        Dialog.resize(238, 42)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setWindowOpacity(53.0)
        self.horizontalLayout = QtGui.QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label = QtGui.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(18)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Turn On The Chiller", None))
        self.label.setText(_translate("Dialog", "Did you turn on the chiller?", None))

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    ex = CCDWindow()
    sys.exit(app.exec_())



























































