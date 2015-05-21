from PyQt4 import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
import scipy.integrate as spi
import re
import time
import os, sys, inspect
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"UIs")))
if cmd_subfolder not in sys.path:
     sys.path.insert(0, cmd_subfolder)
from Abs_ui import Ui_Abs
from HSG_ui import Ui_HSG
from PL_ui import Ui_PL
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
from image_spec_for_gui import *
from InstsAndQt.customQt import TempThread

import logging
log = logging.getLogger("EMCCD")


class BaseExpWidget(QtGui.QWidget):
    # Flags which help to initialize UI settings
    # Need to be set in subclass BEFORE calling def __init__()
    hasNIR = None
    hasFEL = None

    # What is the class in which data will be stored?
    DataClass = EMCCD_image

    sigStartTimer = QtCore.pyqtSignal()


    # data cannot be updated from outside the main thread
    # This general signal can be used to update any images
    # with any data
    # First arg = function to update, second arg = data
    sigUpdateGraphs = QtCore.pyqtSignal(object, object)

    # Cannot create gui items from outside the main thread
    # (i.e. dialog boxes)
    # Use this signal to emit a function to call and the arguments
    # The second signal is used to kill an eventloop wait
    # The expectation is that the emitted value is the return value
    sigMakeGui = QtCore.pyqtSignal(object, object)
    sigKillEventLoop = QtCore.pyqtSignal(object)
    def __init__(self, parent = None, UI=None):
        super(BaseExpWidget, self).__init__(parent)
        self.baseInitUI(UI)

        # Need to keep track of the parent mainwindow so
        # that they can communicate. self.parent() does weird thigns
        # with returning the directly superior widget which is unhelpful
        # for this purpose.
        self.papa = parent

        self.runSettings = dict() # For keeping various information during the run
        self.runSettings["seriesNo"] = 0
        self.runSettings["exposing"] = False

        self.exposureElapsedTimer = QtCore.QElapsedTimer() # For keeping the progress bar correct

        self.thDoExposure = TempThread()
        self.thUpdateProg = TempThread()

        self.thDoContinuous = TempThread()

        # these are necessary for experiments which calculate field strength/
        # intensity with the FEL
        self.thCalcFields = TempThread(target = self.calcFieldValuesLoop)
        self.elWaitForOsc = QtCore.QEventLoop()

        self.curDataEMCCD = None
        self.curBackEMCCD = None
        self.prevDataEMCCD = None

        # The progress bar has timers, which can't be started
        # from another thread. This signal can be used
        # to tell it to start from another thread.
        self.sigStartTimer.connect(self.startProgressBar)

        self.sigUpdateGraphs[object, object].connect(
            lambda img, data: img(data)
        )
        self.sigMakeGui.connect(self.createGuiElement)

    def baseInitUI(self, UI=None):
        # Initialize the UI. pass it the UI class from which it should be made
        self.ui = UI()
        self.ui.setupUi(self)

        # Setting up the splitter regions to be the size I want.
        # I think the names will be general. Care must be taken
        # if/when making new widgets from scratch, if they don't
        # fit this motif
        self.ui.splitterImages.setStretchFactor(0, 1)
        self.ui.splitterImages.setStretchFactor(1, 1)

        self.ui.splitterTop.setStretchFactor(0, 1)
        self.ui.splitterTop.setStretchFactor(1, 10)

        self.ui.splitterAll.setStretchFactor(0, 5)
        self.ui.splitterAll.setStretchFactor(1, 50)
        self.ui.splitterAll.setStretchFactor(2, 2)

        self.ui.tCCDImageNum.textAccepted.connect(
            lambda: self.updateImageNumbers(True))
        self.ui.tCCDBGNum.textAccepted.connect(
            lambda: self.updateImageNumbers(False))


        # Connect the two standard image collection schemes
        self.ui.bCCDImage.clicked.connect(lambda: self.takeImage(False))
        self.ui.bCCDBack.clicked.connect(lambda: self.takeImage(True))

        # Need to tell main window when these settings have changed so it
        # can track them.

        # Note: I'm not sure the best way to do this.
        # dicts can be "passed" by reference
        #    ( self.dic = self.papa.dic)
        # and I could avoid having to always reference
        # self.papa.settings, but these connections would still
        # have to be made.
        #
        # I guess this has the benefit of clearly separating
        # settings held by the parent and those by the widget
        self.ui.tCCDSeries.editingFinished.connect(
                lambda self=self: self.papa.settings.__setitem__('series',
                    str(self.ui.tCCDSeries.text())))
        self.ui.tCCDSampleTemp.editingFinished.connect(
                lambda: self.papa.settings.__setitem__('sample_temp',
                         int(self.ui.tCCDSampleTemp.text())))
        self.ui.tCCDYMin.editingFinished.connect(
                lambda : self.papa.settings.__setitem__('y_min',
                        int(self.ui.tCCDYMin.text())))
        self.ui.tCCDYMax.editingFinished.connect(
                lambda : self.papa.settings.__setitem__('y_max',
                        int(self.ui.tCCDYMax.text())))
        self.ui.tCCDSlits.editingFinished.connect(
                lambda: self.papa.settings.__setitem__('slits',
                        int(self.ui.tCCDSlits.text())))

        if self.hasNIR:
            self.ui.tCCDNIRwavelength.textAccepted.connect(self.parseNIRL)
            self.ui.tCCDNIRwavelength.textAccepted.connect(
                lambda v: self.papa.settings.__setitem__('nir_lambda', v))
            self.ui.tCCDNIRP.textAccepted.connect(
                lambda v: self.papa.settings.__setitem__('nir_power', v))

        if self.hasFEL:
            self.ui.tCCDFELP.textAccepted.connect(
                lambda v: self.papa.settings.__setitem__('fel_power', v))
            self.ui.tCCDFELFreq.textAccepted.connect(
                lambda v: self.papa.settings.__setitem__('fel_lambda', v))
            self.ui.tCCDFELRR.editingFinished.connect(
                lambda: self.papa.settings.__setitem__('fel_reprate',
                                     str(self.ui.tCCDFELRR.text())))
            self.ui.tCCDSpotSize.textAccepted.connect(
                lambda v: self.papa.settings.__setitem__('sample_spot_size', v))
            self.ui.tCCDWindowTransmission.textAccepted.connect(
                lambda v: self.papa.settings.__setitem__('window_trans', v))
            self.ui.tCCDEffectiveField.textAccepted.connect(
                lambda v: self.papa.settings.__setitem__('eff_field', v))


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
        # plotitem = self.ui.gCCDBin.getPlotItem()
        plotitem = self.ui.gCCDBin.plotItem
        plotitem.setTitle('Spectrum')
        plotitem.setLabel('bottom',text='Wavelength',units='nm')
        plotitem.setLabel('left',text='Counts')

        # These are infinite lines for when taking a continuous
        # image. Issues arise if you try to make them in
        # another thread.
        self.ilOnep1 = pg.InfiniteLine(800, movable=True,
                                     pen=pg.mkPen(width=3, color='g'))
        self.ilTwop1 = pg.InfiniteLine(800, movable=True,
                                     pen=pg.mkPen(width=3, color='g'))
        self.ilOnep2 = pg.InfiniteLine(760, movable=True,
                                     pen=pg.mkPen(width=3, color='g'))
        self.ilTwop2 = pg.InfiniteLine(760, movable=True,
                                     pen=pg.mkPen(width=3, color='g'))

    @staticmethod
    def __IMAGE_COLLECTION_METHODS(): pass

    def takeImage(self, isBackground = False):
        self.thDoExposure.target = self.doExposure

        # Tell the thread what function to call after it
        # gets the data. This ensures the processing
        # is maintained in that thread

        # In the future, may want to provide your
        # own function to call when finished with the
        # exposure, so we test for that first
        if hasattr(isBackground, "__call__"):
            self.thDoExposure.args = isBackground
        else:
            self.thDoExposure.args = self.processImage
            if isBackground:
                self.thDoExposure.args = self.processBackground
        # Turn off UI elements to prevent conflicts
        # For some reson, if you do this in the thread,
        # Qt complains about starting timers in threads.
        # I could not figure out the source of this error, so
        # I ignore it
        self.exposureElapsedTimer = QtCore.QElapsedTimer()
        self.toggleUIElements(False)

        if self.hasFEL:
            self.runSettings["fieldStrength"] = []
            self.runSettings["fieldInt"] = []
            self.ui.tCCDFELPulses.setText("0")
            self.papa.oscWidget.ui.tOscPulses.setText("0")
            self.papa.oscWidget.settings["FELPulses"] = 0
        self.thDoExposure.start()


    def doExposure(self, postProcessing = lambda: True):
        """
        This function should be called when you want to handle taking an image
        It checks the exposure/gain, sets them if necessary. Sets up timing to wait for
        completion of the image, etc

        This thread WILL hang. Do not call from main thread

        :return: the data from the camera, unmodified
        """

        self.runSettings["progress"] = 0
        # Update exposure/gain if necesssary
        if not np.isclose(float(self.ui.tEMCCDExp.value()), self.papa.CCD.cameraSettings["exposureTime"]):
            self.papa.CCD.setExposure(float(self.ui.tEMCCDExp.text()))
        if not int(self.ui.tEMCCDGain.text()) == self.papa.CCD.cameraSettings["gain"]:
            self.papa.CCD.setGain(int(self.ui.tEMCCDGain.text()))


        self.papa.CCD.dllStartAcquisition()
        if self.hasFEL and not self.papa.oscWidget.settings["isScopePaused"] and not self.papa.ui.mFileTakeContinuous.isChecked():
            waitForPulseLoop = QtCore.QEventLoop()
            self.papa.oscWidget.updateOscDataSig.connect(waitForPulseLoop.exit)
            waitForPulseLoop.exec_()

        self.runSettings["exposing"] = True
        if self.hasFEL and not self.papa.ui.mFileTakeContinuous.isChecked():
            self.thCalcFields.start()
        if not self.papa.ui.mFileTakeContinuous.isChecked():
            self.sigStartTimer.emit()
        self.papa.CCD.dllWaitForAcquisition()
        self.runSettings["exposing"] = False
        if self.hasFEL and not self.papa.ui.mFileTakeContinuous.isChecked():
            try:
                self.elWaitForOsc.exit()
            except:
                log.debug("Error exiting eventLoop waiting for pulses")
        self.rawData = self.papa.CCD.getImage()
        postProcessing()

    def startProgressBar(self):
        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Waiting exposure")
        self.exposureElapsedTimer.start()

        QtCore.QTimer.singleShot(self.papa.CCD.cameraSettings["exposureTime"]*10,
                                 self.updateProgressBar)

    def updateProgressBar(self):
        if self.runSettings["progress"] < 100:
            self.runSettings["progress"] += 1
            self.ui.pCCD.setValue(self.runSettings["progress"])
            # Get the new time, correcting for lags and other things
            # which deviate from expected.
            newTime = ((self.runSettings["progress"] + 1) * self.papa.CCD.cameraSettings["exposureTime"]*10) \
                      - (self.exposureElapsedTimer.elapsed())

            # Sometimes things take so long, it wants us to go back in time,
            # which we can't yet do.
            if newTime < 0:
                newTime = 0
            try:
                QtCore.QTimer.singleShot(newTime,
                                         self.updateProgressBar)
            except:
                log.critical("Didn't update progress ")
        else:
            self.papa.updateElementSig.emit(self.ui.lCCDProg, "Reading Data")
            self.runSettings["exposing"] = False
            self.exposureElapsedTimer = None

    def startContinuous(self, value):
        if value:
            self.runSettings["takingContinuous"] = True
            self.p1.addItem(self.ilOnep1)
            self.p1.addItem(self.ilTwop1)
            self.ui.gCCDBin.plotItem.addItem(self.ilOnep2)
            self.ui.gCCDBin.plotItem.addItem(self.ilTwop2)
            self.takeImage(isBackground = self.takeContinuousLoop)

    def takeContinuousLoop(self):
        while self.papa.ui.mFileTakeContinuous.isChecked():
            self.sigUpdateGraphs.emit(self.updateSignalImage, self.rawData)
            image = EMCCD_image(self.rawData,
                                "", "", "", self.genEquipmentDict())
            image.clean_array = image.raw_array
            image.make_spectrum()
            self.sigUpdateGraphs.emit(self.updateSpectrum, image.spectrum)
            self.doExposure()
        self.toggleUIElements(True)
        self.p1.removeItem(self.ilOnep1)
        self.p1.removeItem(self.ilTwop1)
        self.runSettings["takingContinuous"] = False

        self.ui.gCCDBin.plotItem.removeItem(self.ilOnep2)
        self.ui.gCCDBin.plotItem.removeItem(self.ilTwop2)


    @staticmethod
    def __PULSE_COUNTING(): pass
    ################################
    #
    # These methods only really matter if the FEL
    # is around
    #
    ################################
    def calcFieldValuesLoop(self):
        self.elWaitForOsc = QtCore.QEventLoop()
        self.papa.oscWidget.sigDoneCounting.connect(self.elWaitForOsc.exit)
        self.elWaitForOsc.exec_()
        self.papa.oscWidget.sigDoneCounting.disconnect(self.elWaitForOsc.exit)
        while self.runSettings["exposing"]:
            try:
                self.doFieldCalcuation(
                    self.papa.oscWidget.settings["pyBG"],
                    self.papa.oscWidget.settings["pyFP"],
                    self.papa.oscWidget.settings["pyCD"]
                )
                # MUST INSTANTIATE IN THREAD
                # Otherwise catastrophic Qt errors arise
                self.elWaitForOsc = QtCore.QEventLoop()
                self.papa.oscWidget.sigDoneCounting.connect(self.elWaitForOsc.exit)
                self.elWaitForOsc.exec_()
                self.papa.oscWidget.sigDoneCounting.disconnect(self.elWaitForOsc.exit)
            except Exception as e:
                print "ERROR ",e


    def doFieldCalcuation(self, BG = 1.0, FP = 2.0, CD = 2.0):
        """
        :param BG: integrated background value
        :param FP: integrated front porch value
        :param CD: integrated cavity dump region
        :return:
        """
        try:
            energy = self.ui.tCCDFELP.value()
            windowTrans = self.ui.tCCDWindowTransmission.value()
            effField = self.ui.tCCDEffectiveField.value()
            radius = self.ui.tCCDSpotSize.value()
            ratio = FP/(FP + CD)
            intensity = calc_THz_intensity(energy, windowTrans, effField, radius=radius,
                                       ratio = ratio)
            field = calc_THz_field(intensity)

            intensity = round(intensity/1000., 3)
            field = round(field/1000., 3)

            self.papa.updateElementSig.emit(
                self.ui.tCCDIntensity, "{:.3f}".format(intensity))
            self.runSettings["fieldInt"].append(intensity)
            self.papa.updateElementSig.emit(
                self.ui.tCCDEField, "{:.3f}".format(field))
            self.runSettings["fieldStrength"].append(field)

        except Exception as e:
            log.warning("Could not calculate electric field, {}".format(e))


    @staticmethod
    def __PROCESSING_METHODS(): pass
        ####################################
        #
        # Concerning the image numbers:
        #
        # Things were getting confusing having an internal variable and the textbox
        # so switched to only using textbox. But this has issue that, since texboxes
        # can't be updated from non-main threads (or it's unpredictable), signals are needed
        # But this has issues that a fast computer will instantiate the object before
        # the text is updated, so they're out of sync (I think, at least).
        #
        # This way, we know that the textbox will be incremented by one,
        # but we forcibly tell it that it's going to be incremented
        # instead of hoping that things will time properly
        #
        ####################################

    def processImage(self):
        self.sigUpdateGraphs.emit(self.updateSignalImage, self.rawData)
        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Cleaning Data")

        self.curDataEMCCD = self.DataClass(self.rawData,
                                            str(self.papa.ui.tImageName.text()),
                                            str(self.ui.tCCDImageNum.value()+1),
                                            str(self.ui.tCCDComments.toPlainText()),
                                            self.genEquipmentDict())

        if self.papa.settings["doCRR"]:
            self.curDataEMCCD.cosmic_ray_removal()
        else:
            self.curDataEMCCD.clean_array = self.curDataEMCCD.raw_array

        try:
            self.curDataEMCCD = self.curDataEMCCD - self.curBackEMCCD
            self.curDataEMCCD.equipment_dict["background_darkcount_std"] = np.std(
                self.curBackEMCCD.clean_array[:, self.curDataEMCCD.equipment_dict["y_min"]:
                                            self.curDataEMCCD.equipment_dict["y_max"]]
            )
        except AttributeError as e:
            log.debug("Attribute error: {}".format(e))
            pass # usually just because you subtract without taking a
                 # background first
        except Exception as e:
            log.warning("Error subtracting background {}".format(e))

        self.curDataEMCCD.make_spectrum()
        self.curDataEMCCD.inspect_dark_regions()

        self.sigUpdateGraphs.emit(self.updateSignalImage, self.curDataEMCCD.clean_array)
        self.sigUpdateGraphs.emit(self.updateSpectrum, self.curDataEMCCD.spectrum)

        # Do we want to keep this image?
        if not self.confirmImage():
            self.papa.updateElementSig.emit(self.ui.lCCDProg, "Done.")
            self.toggleUIElements(True)
            return

        try:
            self.curDataEMCCD.save_images(self.papa.settings["saveDir"])
            self.papa.sigUpdateStatusBar.emit("Saved Image: {}".format(self.ui.tCCDImageNum.value()+1))
        except Exception as e:
            self.papa.sigUpdateStatusBar.emit("Error saving image")
            log.warning("Error saving Data image, {}".format(e))

        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Finishing Up...")
        try:
            self.curDataEMCCD.save_spectrum(self.papa.settings["saveDir"])
            self.papa.sigUpdateStatusBar.emit("Saved Spectrum: {}".format(self.ui.tCCDImageNum.value()+1))
            # incrememnt the counter, but certainly after we're done with it
            self.papa.updateElementSig.emit(self.ui.tCCDImageNum, self.ui.tCCDImageNum.value()+1)
        except Exception as e:
            self.papa.sigUpdateStatusBar.emit("Error saving Spectrum")
            log.warning("Error saving Data Spectrum, {}".format(e))

        if self.papa.ui.mSeriesSum.isChecked() and str(self.ui.tCCDSeries.text())!="":
            self.papa.updateElementSig.emit(self.ui.lCCDProg, "Adding Series...")
            self.analyzeSeries()
        else:
            self.prevDataEMCCD = None
            self.runSettings["seriesNo"] = 0
            self.ui.groupBox_42.setTitle("Series")
        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Done.")
        self.toggleUIElements(True)



    def processBackground(self):
        self.sigUpdateGraphs.emit(self.updateBackgroundImage, self.rawData)
        self.toggleUIElements(True)
        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Cleaning Data")

        self.curBackEMCCD = self.DataClass(self.rawData,
                                            str(self.papa.ui.tBackgroundName.text()),
                                            str(self.ui.tCCDBGNum.value()+1),
                                            str(self.ui.tCCDComments.toPlainText()),
                                            self.genEquipmentDict())

        try:
            self.curBackEMCCD.save_images(self.papa.settings["saveDir"])
            self.papa.sigUpdateStatusBar.emit("Saved Background: {}".format(self.ui.tCCDBGNum.value()+1))
            # incrememnt the counter, but certainly after we're done with it
            self.papa.updateElementSig.emit(self.ui.tCCDBGNum, self.ui.tCCDBGNum.value()+1)
        except Exception as e:
            self.papa.sigUpdateStatusBar.emit("Error saving image")
            log.warning("Error saving Data image, {}".format(e))

        if self.papa.settings["doCRR"]:
            self.curBackEMCCD.cosmic_ray_removal()
        else:
            self.curBackEMCCD.clean_array = self.curBackEMCCD.raw_array
        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Finishing up...")

        self.curBackEMCCD.make_spectrum()
        self.curBackEMCCD.inspect_dark_regions()

        self.sigUpdateGraphs.emit(self.updateBackgroundImage, self.curBackEMCCD.clean_array)
        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Done.")

    def confirmImage(self):
        """
        Prompts the user to ensure the most recent image is acceptable.
        :return: Boolean of whether or not to accept.
        """
        loop = QtCore.QEventLoop()
        self.sigKillEventLoop.connect(lambda v: loop.exit(v))
        self.sigMakeGui.emit(
            QtGui.QMessageBox.information, (
            None,"Confirm",
            """Save most recent scan?""",
            QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard,
            QtGui.QMessageBox.Save
        )
        )
        ret = loop.exec_()
        return ret == QtGui.QMessageBox.Save
        # return True


    def analyzeSeries(self):
        #######################
        # Handling of series tag to add things up live
        #
        # Want it to save only the latest series, but also
        # the previous ones should be saved (hence why this is
        # after the saving is being done)
        #######################
        if (self.prevDataEMCCD is not None and
                    self.prevDataEMCCD.equipment_dict["series"] ==
                    self.curDataEMCCD.equipment_dict["series"]):
            log.debug("Added two series together")
            # Un-normalize by the number currently in series
            self.prevDataEMCCD.clean_array*=self.runSettings["seriesNo"]

            try:
                self.prevDataEMCCD += self.curDataEMCCD
            except Exception as e:
                log.debug("Error adding series data, {}".format(e))
            else:
                self.papa.ui.mSeriesUndo.setEnabled(True)

            self.prevDataEMCCD.make_spectrum()

            # Save the summed, unnormalized spectrum
            try:
                self.prevDataEMCCD.save_spectrum(self.papa.settings["saveDir"])
                self.papa.sigUpdateStatusBar.emit("Saved Series")
            except Exception as e:
                self.papa.sigUpdateStatusBar.emit("Error Saving Series")
                log.debug("Error saving series data, {}".format(e))

            self.runSettings["seriesNo"] +=1
            self.ui.groupBox_42.setTitle("Series ({})".format(self.runSettings["seriesNo"]))
            # but PLOT the normalized average
            self.prevDataEMCCD.spectrum[:,1]/=self.runSettings["seriesNo"]
            self.prevDataEMCCD.clean_array/=self.runSettings["seriesNo"]

            # Update the plots with this new data
            self.sigUpdateGraphs.emit(self.updateSignalImage, self.prevDataEMCCD.clean_array)
            self.sigUpdateGraphs.emit(self.updateSpectrum, self.prevDataEMCCD.spectrum)

        elif str(self.ui.tCCDSeries.text()) != "":
            self.prevDataEMCCD = copy.deepcopy(self.curDataEMCCD)
            self.prevDataEMCCD.file_no += "seriesed"
            self.runSettings["seriesNo"] = 1
            self.ui.groupBox_42.setTitle("Series (1)")


        else:
            self.prevDataEMCCD = None
            self.runSettings["seriesNo"] = 0
            self.ui.groupBox_42.setTitle("Series")
            log.debug("Made a new series where I didn't think I'd be")

    def undoSeries(self):
        log.debug("Added two series together")
        # Un-normalize by the number currently in series
        self.prevDataEMCCD.clean_array *= self.runSettings["seriesNo"]

        try:
            self.prevDataEMCCD -= self.curDataEMCCD
        except Exception as e:
            log.debug("Error undoing series data, {}".format(e))
        else:
            self.papa.ui.mSeriesUndo.setEnabled(False)

        self.prevDataEMCCD.make_spectrum()

        # Save the summed, unnormalized spectrum
        try:
            self.prevDataEMCCD.save_spectrum(self.papa.settings["saveDir"])
            self.papa.sigUpdateStatusBar.emit("Saved Series")
        except Exception as e:
            self.papa.sigUpdateStatusBar.emit("Error Saving Series")
            log.debug("Error saving series data, {}".format(e))

        self.runSettings["seriesNo"] -=1
        self.ui.groupBox_42.setTitle("Series ({})".format(self.runSettings["seriesNo"]))
        # but PLOT the normalized average
        self.prevDataEMCCD.spectrum[:,1]/=self.runSettings["seriesNo"]
        self.prevDataEMCCD.clean_array/=self.runSettings["seriesNo"]

        # Update the plots with this new data
        self.sigUpdateGraphs.emit(self.updateSignalImage, self.prevDataEMCCD.clean_array)
        self.sigUpdateGraphs.emit(self.updateSpectrum, self.prevDataEMCCD.spectrum)


    def genEquipmentDict(self):
        """
        The EMCCD class wants a specific dictionary of values. This function will return it
        :return:
        """
        s = dict()
        s["ccd_temperature"] = str(self.papa.ui.tSettingsCurrTemp.text())
        s["exposure"] = float(self.papa.CCD.cameraSettings["exposureTime"])
        s["gain"] = int(self.papa.CCD.cameraSettings["gain"])
        s["y_min"] = int(self.ui.tCCDYMin.text())
        s["y_max"] = int(self.ui.tCCDYMax.text())
        s["grating"] = int(self.papa.ui.sbSpecGrating.value())
        s["center_lambda"] = float(self.papa.ui.sbSpecWavelength.value())
        s["slits"] = str(self.ui.tCCDSlits.text())
        s["dark_region"] = None
        s["bg_file_name"] = str(self.papa.ui.tBackgroundName.text()) + str(self.ui.tCCDBGNum.value())
        s["sample_Temp"] = str(self.ui.tCCDSampleTemp.text())
        s["sample_name"] = str(self.ui.tSampleName.text())

        # If the user has the series box as {<variable>} where variable is
        # any of the keys below, we want to replace it with the relavent value
        # Potentially unnecessary at this point...
        st = str(self.ui.tCCDSeries.text())
        st = st.format(SLITS=s["slits"], SPECL = s["center_lambda"],
                       GAIN=s["gain"], EXP=s["exposure"])
        if self.hasFEL:
            s["fel_power"] = str(self.ui.tCCDFELP.text())
            s["fel_reprate"] = str(self.ui.tCCDFELRR.text())
            s["fel_lambda"] = str(self.ui.tCCDFELFreq.text())
            s["fel_pulses"] = int(self.ui.tCCDFELPulses.text()) if \
                str(self.ui.tCCDFELPulses.text()).strip() else 0
            s["fieldStrength"] = self.runSettings["fieldStrength"]
            s["fieldInt"] = self.runSettings["fieldInt"]

            st = st.format(FELF=s["fel_lambda"], FELP=s["fel_power"])

        if self.hasNIR:
            s["nir_power"] = str(self.ui.tCCDNIRP.text())
            s["nir_lambda"] = str(self.ui.tCCDNIRwavelength.text())

            st = st.format(NIRP=s["nir_power"], NIRW=s["nir_lambda"])


        s["series"] = st
        return s




    @staticmethod
    def __BASIC_UI_CHANGES(): pass

    def toggleUIElements(self, enabled = True):
        """
        Function to enable/disable buttons
        :param enabled: To enable or disable elements
        :return:
        """
        self.ui.bCCDBack.setEnabled(enabled)
        self.ui.bCCDImage.setEnabled(enabled)
        self.papa.ui.gbSettings.setEnabled(enabled)


    def updateSignalImage(self, data = None):
        data = np.array(data)
        self.pSigImage.setImage(data)
        self.pSigHist.setLevels(data.min(), data.max())

    def updateBackgroundImage(self, data = None):
        data = np.array(data)
        self.pBackImage.setImage(data)
        self.pBackHist.setLevels(data.min(), data.max())


    def updateSpectrum(self, data = None):
        self.pSpec.setData(data[:,0], data[:,1])

    def parseNIRL(self):
        """
        We want wavelength, but sometimes we're working with wavenumber
        It'd be nice to do the calculation in the software
        :return:
        """
        val = self.ui.tCCDNIRwavelength.value()
        if val>1500:
            self.ui.tCCDNIRwavelength.setText("{:.3f}".format(10000000./val))

    def updateImageNumbers(self, isIm = True):
        """
        :param sender: flag for who sent
        :return:
        allow the user to update the image number counters
        """
        if isIm:
            self.papa.settings["igNumber"] = int(self.ui.tCCDImageNum.text())
        else:
            self.papa.settings["bgNumber"] = int(self.ui.tCCDBGNum.text())

    def createGuiElement(self, fnc, args):
        ret = fnc(*args)
        self.sigKillEventLoop.emit(ret)


class HSGWid(BaseExpWidget):
    hasNIR = True
    hasFEL = True

    DataClass = HSG_image
    def __init__(self, parent = None):
        super(HSGWid, self).__init__(parent, Ui_HSG)
        self.initUI()


    def initUI(self):
        # Set up the things for the slider which tells you
        # what sideband you're on
        self.ilSpec = pg.InfiniteLine(movable=True,
                                     pen=pg.mkPen(width=2, color='g'))
        self.ilSpec.sigPositionChanged.connect(self.updateSBfromLine)
        self.ui.gCCDBin.addItem(self.ilSpec)
        self.ui.tCCDSidebandNumber.textAccepted.connect(self.updateSBfromValue)

    def updateSBfromLine(self):
        try:
            wn = 10000000./self.ui.tCCDNIRwavelength.value()
            wanted = 10000000./self.ilSpec.value()
            sbn = (wanted-wn)/self.ui.tCCDFELFreq.value()
            # Need to disconnect/reconnect here, otherwise they call each other infinitely
            self.ui.tCCDSidebandNumber.textAccepted.disconnect(self.updateSBfromValue)
            self.ui.tCCDSidebandNumber.setText("{:.3f}".format(sbn))
            self.ui.tCCDSidebandNumber.textAccepted.connect(self.updateSBfromValue)
        except Exception as e:
            if type(e) is ZeroDivisionError:
                return
            log.warning("Could not update SB line, {}".format(e))


    def updateSBfromValue(self):
        try:
            wn = 10000000./self.ui.tCCDNIRwavelength.value()
            wanted = wn + self.ui.tCCDSidebandNumber.value()*self.ui.tCCDFELFreq.value()
            wanted = 10000000./wanted
            # Need to disconnect/reconnect here, otherwise they call each other infinitely
            self.ilSpec.sigPositionChanged.disconnect(self.updateSBfromLine)
            self.ilSpec.setValue(wanted)
            self.ilSpec.sigPositionChanged.connect(self.updateSBfromLine)
        except Exception as e:
            log.warning("Could not update SB line from inputted value, {}".format(e))


class AbsWid(BaseExpWidget):
    hasNIR = False
    hasFEL = False

    DataClass = Abs_image
    def __init__(self, parent = None):
        super(AbsWid, self).__init__(parent, Ui_Abs)
        self.initUI()
        self.curRefEMCCD = None
        self.curAbsEMCCD = None # holds the actual absorption

    def initUI(self):
        self.ui.bCCDReference.clicked.connect(self.takeReference)
        self.ui.tCCDRefNum.textAccepted.connect(
            lambda: self.papa.settings.__setitem__("rfNumber",self.ui.tCCDRefNum.value()))

        # for plotting the raw spectra
        self.pRawvb = pg.ViewBox()
        self.ui.gCCDBin.plotItem.showAxis("right")
        self.ui.gCCDBin.plotItem.scene().addItem(self.pRawvb)
        self.ui.gCCDBin.plotItem.getAxis("right").linkToView(self.pRawvb )
        self.pRawvb.setXLink(self.ui.gCCDBin.plotItem)
        self.ui.gCCDBin.plotItem.getAxis("right").setLabel("Raw Counts")

        self.updateGraphViews()
        self.ui.gCCDBin.plotItem.vb.sigResized.connect(self.updateGraphViews)
        self.pRawBlank = pg.PlotCurveItem(pen="r")
        self.pRawTrans = pg.PlotCurveItem(pen="b")
        self.pRawvb.addItem(self.pRawBlank)
        self.pRawvb.addItem(self.pRawTrans)

    def takeReference(self):
        self.takeImage(isBackground = self.processReference)

    def processImage(self):
        super(AbsWid, self).processImage()
        if self.curRefEMCCD is None or not self.curRefEMCCD==self.curDataEMCCD:
            self.papa.sigUpdateStatusBar.emit("Please take a reference with the same settings")
            log.warning("Please take a reference with the same settings")
            return
        else:
            self.curDataEMCCD.equipment_dict["reference_file"] = self.curRefEMCCD.getFileName()
            self.curAbsEMCCD = self.curRefEMCCD/self.curDataEMCCD
            try:
                self.curAbsEMCCD.save_spectrum(folder_str=self.papa.settings["saveDir"], prefix="abs_")
            except Exception as e:
                self.papa.sigUpdateStatusBar.emit("Error saving Absorbance")
                log.warning("Error saving Absorbance Spectrum, {}".format(e))
            self.sigUpdateGraphs.emit(self.updateSpectrum, self.curAbsEMCCD)


    def processBackground(self):
        super(AbsWid, self).processBackground()

    def processReference(self):
        self.sigUpdateGraphs.emit(self.updateSignalImage, self.rawData)
        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Cleaning Data")

        self.curRefEMCCD = self.DataClass(self.rawData,
                                            str(self.papa.ui.tImageName.text()),
                                            str(self.ui.tCCDRefNum.value()+1),
                                            str(self.ui.tCCDComments.toPlainText()),
                                            self.genEquipmentDict())

        try:
            self.curRefEMCCD.save_images(self.papa.settings["saveDir"], prefix="absBlank_")
            self.papa.sigUpdateStatusBar.emit("Saved reference: {}".format(self.ui.tCCDRefNum.value()+1))
        except Exception as e:
            self.papa.sigUpdateStatusBar.emit("Error saving reference")
            log.warning("Error saving reference image, {}".format(e))

        if self.papa.settings["doCRR"]:
            self.curRefEMCCD.cosmic_ray_removal()
        else:
            self.curRefEMCCD.clean_array = self.curRefEMCCD.raw_array

        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Finishing Up...")

        try:
            self.curRefEMCCD = self.curRefEMCCD - self.curBackEMCCD
        except AttributeError as e:
            pass # usually just because you subtract without taking a
                 # background first
        except Exception as e:
            log.warning("Error subtracting background {}".format(e))

        self.curRefEMCCD.make_spectrum()
        self.curRefEMCCD.inspect_dark_regions()
        try:
            self.curRefEMCCD.save_spectrum(self.papa.settings["saveDir"], prefix="absBlank_")
            self.papa.sigUpdateStatusBar.emit("Saved Spectrum: {}".format(self.ui.tCCDRefNum.value()+1))
            # incrememnt the counter, but certainly after we're done with it
            self.papa.updateElementSig.emit(self.ui.tCCDRefNum, self.ui.tCCDRefNum.value()+1)
        except Exception as e:
            self.papa.sigUpdateStatusBar.emit("Error saving reference Spectrum")
            log.warning("Error saving reference Spectrum, {}".format(e))


        self.sigUpdateGraphs.emit(self.updateSignalImage, self.curRefEMCCD)
        self.sigUpdateGraphs.emit(self.updateSpectrum, self.curRefEMCCD)
                        # if self.papa.ui.mSeriesSum.isChecked() and str(self.ui.tCCDSeries.text())!="":
            #HOW SHOULD THIS BE HANDLED FOR REFERENCE?
                        #     self.papa.updateElementSig.emit(self.ui.lCCDProg, "Adding Series...")
                        #     self.analyzeSeries()
                        # else:
                        #     self.prevDataEMCCD = None
                        #     self.runSettings["seriesNo"] = 0
                        #     self.ui.groupBox_42.setTitle("Series")
        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Done.")
        self.toggleUIElements(True)

    def analyzeSeries(self):
        log.info("Note: Series not implemented for Absorption data")

    def updateGraphViews(self):
        self.pRawvb.setGeometry(self.ui.gCCDBin.plotItem.vb.sceneBoundingRect())
        self.pRawvb.linkedViewChanged(self.ui.gCCDBin.plotItem.vb,
                                      self.pRawvb.XAxis)


    def toggleUIElements(self, enabled = True):
        super(AbsWid, self).toggleUIElements(enabled)
        self.ui.bCCDReference.setEnabled(enabled)

    def updateSignalImage(self, data = None):
        title = "Transmission"
        if id(data) == id(self.curRefEMCCD):
            data = self.curRefEMCCD.clean_array
            title = "Blank"
        super(AbsWid, self).updateSignalImage(data)
        pi = self.ui.gCCDImage.getItem(0,0)
        pi.setTitle(title)


    def updateSpectrum(self, data = None):
        title = "Transmission"
        # Need to use id() because we've overloaded __eq__ for the
        # data class to check for camera settings
        if id(data) == id(self.curAbsEMCCD):
            print "called with abs"
            self.pSpec.setData(self.curAbsEMCCD.spectrum[:,0], self.curAbsEMCCD.spectrum[:,3])
            self.pRawBlank.setData(self.curAbsEMCCD.spectrum[:,0], self.curAbsEMCCD.spectrum[:,1])
            self.pRawTrans.setData(self.curAbsEMCCD.spectrum[:,0], self.curAbsEMCCD.spectrum[:,2])
        elif id(data)==id(self.curRefEMCCD):
            title = "Blank"
            print "called with ref"
            data = self.curRefEMCCD.spectrum
            self.pRawBlank.setData(data[:,0], data[:,1])
            self.pSpec.setData([], [])
            self.pRawTrans.setData([], [])
        else:
            print "called with else (img?)"
            self.pRawTrans.setData(data[:,0], data[:,1])
            self.updateGraphViews()

        # super(AbsWid, self).updateSpectrum(data)
        # pi = self.ui.gCCDBin.getPlotItem()
        # pi.setTitle(title)


class PLWid(BaseExpWidget):
    hasNIR = True
    hasFEL = False

    DataClass = PL_image
    def __init__(self, parent = None):
        super(PLWid, self).__init__(parent, Ui_PL)

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    ex = AbsWid()
    ex.show()
    sys.exit(app.exec_())