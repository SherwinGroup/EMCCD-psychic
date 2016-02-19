from PyQt4 import QtGui, QtCore
import pyqtgraph as pg
from scipy.interpolate import interp1d
import time
import hsganalysis as hsg
from UIs.Abs_ui import Ui_Abs
from UIs.HSG_ui import Ui_HSG
from UIs.PL_ui import Ui_PL
from UIs.TwoColorAbs_ui import Ui_TwoColorAbs
from UIs.Alignment_ui import Ui_Alignment
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
import hsganalysis as hsg
from image_spec_for_gui import *
from InstsAndQt.customQt import *

import logging
log = logging.getLogger("EMCCD")


seriesTags = {"SLITS": "slits",
              "SPECL": "center_lambda",
              "GAIN": "gain",
              "EXP": "exposure",
              "FELF": "fel_lambda",
              "FELP": "fel_power",
              "NIRP": "nir_power",
              "NIRW": "nir_lambda",
              "FELTRANS": "fel_transmission"}


class CustomAxis(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(CustomAxis, self).__init__(*args, **kwargs)
        self.dataSet = None
        self.dataSetInterp = None

    def tickStrings(self, values, scale, spacing):
        if self.dataSet is None:
            return super(CustomAxis, self).tickStrings(
                values=values,
                scale=scale,
                spacing=spacing
            )
        else:
            return ['{:.0f}'.format(float(self.dataSetInterp(i))) for i in values]

    def setDataSet(self, data):
        self.dataSet = data
        if callable(data):
            # let you pass a function
            self.dataSetInterp = data
        elif data is not None:
            self.dataSetInterp = interp1d(x=data,
                                          y=np.arange(len(data)),
                                          bounds_error=False,
                                          fill_value = -1)

class BaseExpWidget(QtGui.QWidget):
    # Flags which help to initialize UI settings
    # Need to be set in subclass BEFORE calling def __init__()
    hasNIR = None
    hasFEL = None

    # What is the class in which data will be stored?
    DataClass = EMCCD_image

    # name to be used for the tab title
    name = 'Base Tab'

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


    # Need to have an instance attribute because if we
    # spawn threads willy-nilly, things end up breaking
    # bad.
    progressTimer = QtCore.QTimer()


    # eventLoop which will be used to wait for
    # confirmation of the image.
    # (pretty sure it needs to be instantiated in
    # the thread it'll be used in, not here)
    eloopConfirmImage = None
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

        self.crrSettings={
            "ratio":0.07,
            "noisecoeff":3.0
        }

        self.exposureElapsedTimer = QtCore.QElapsedTimer() # For keeping the progress bar correct

        self.thDoExposure = TempThread()
        self.thUpdateProg = TempThread()

        self.thDoContinuous = TempThread()

        # these are necessary for experiments which calculate field strength/
        # intensity with the FEL
        self.elWaitForOsc = QtCore.QEventLoop()

        self.curDataEMCCD = None
        self.curBackEMCCD = None
        self.prevDataEMCCD = None
        self.prevBackEMCCD = None

        # The progress bar has timers, which can't be started
        # from another thread. This signal can be used
        # to tell it to start from another thread.
        self.sigStartTimer.connect(self.startProgressBar)

        self.sigUpdateGraphs[object, object].connect(
            lambda img, data: img(data)
        )
        self.sigMakeGui.connect(self.createGuiElement)

    def baseInitUI(self, UI=Ui_HSG):
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
            lambda: self.papa.settings.__setitem__("igNumber",self.ui.tCCDImageNum.value()))
        self.ui.tCCDBGNum.textAccepted.connect(
            lambda: self.papa.settings.__setitem__("bgNumber",self.ui.tCCDBGNum.value()))

        # self.ui.tCCDImageNum.textAccepted.connect(
        #     lambda: self.updateImageNumbers(True))
        # self.ui.tCCDBGNum.textAccepted.connect(
        #     lambda: self.updateImageNumbers(False))


        # Connect the two standard image collection schemes
        self.ui.bCCDImage.clicked.connect(lambda: self.takeImage(False))
        self.ui.bCCDBack.clicked.connect(lambda: self.takeImage(True))

        self.ui.bProcessImageSequence.clicked.connect(self.processImageSequence)
        self.ui.bProcessBackgroundSequence.clicked.connect(self.processBackgroundSequence)

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
                                                   float(self.ui.tCCDSampleTemp.text())))
        self.ui.tCCDYMin.editingFinished.connect(
            lambda : self.papa.settings.__setitem__('y_min',
                                                    int(self.ui.tCCDYMin.text())))
        self.ui.tCCDYMax.editingFinished.connect(
            lambda : self.papa.settings.__setitem__('y_max',
                                                    int(self.ui.tCCDYMax.text())))
        self.ui.tCCDSlits.editingFinished.connect(
            lambda: self.papa.settings.__setitem__('slits',
                                                   int(self.ui.tCCDSlits.text())))
        self.ui.tSampleName.editingFinished.connect(
            lambda: self.papa.settings.__setitem__("sample_name",
                                                   str(self.ui.tSampleName.text()))
        )

        if self.hasNIR:
            self.ui.tCCDNIRwavelength.textAccepted.connect(self.parseNIRL)
            self.ui.tCCDNIRwavelength.textAccepted.connect(
                lambda v: self.papa.settings.__setitem__('nir_lambda', v))
            self.ui.tCCDNIRP.textAccepted.connect(
                lambda v: self.papa.settings.__setitem__('nir_power', v))
            self.ui.tCCDNIRPol.editingFinished.connect(
                lambda: self.papa.settings.__setitem__("nir_pol",
                                                       str(self.ui.tCCDNIRPol.text()))
            )

        # add autocompleter functionality so you
        # know what series tags can automatically be used
        words = ["{"+ii+"}" for ii in seriesTags]
        comp = QtGui.QCompleter(words, self)
        self.ui.tCCDSeries.setCompleter(comp)


        self.ui.gCCDBack.view.setAspectLocked(False)
        self.ui.gCCDBack.view.invertY(False)

        self.ui.gCCDImage.view.setAspectLocked(False)
        self.ui.gCCDImage.view.invertY(False)


        self.pSpec = self.ui.gCCDBin.plot(pen='k')

        plotitem = self.ui.gCCDBin.plotItem
        plotitem.setLabel('bottom',text='Wavelength',units='nm')
        plotitem.setLabel('left',text='Counts')
        # plotitem.setLabel('top', text='pixels')


        plotitem.layout.removeItem(plotitem.getAxis('top'))
        caxis = CustomAxis(orientation='top', parent=plotitem)
        caxis.setLabel('Pixel')
        caxis.linkToView(plotitem.vb)
        plotitem.axes['top']['item'] = caxis
        plotitem.layout.addItem(caxis, 1, 1)




        # specified that the view for the image is
        # a plotitem, so I can have axis. Get it back
        plotitem = self.ui.gCCDImage.getView()

        # need to set up custom axis item so that
        # I can add functionality to show the pixel
        # number along with wavelength, for comparison
        # with the real image
        plotitem.layout.removeItem(plotitem.getAxis('right'))
        caxis = CustomAxis(orientation='right', parent=plotitem)
        caxis.linkToView(plotitem.vb)
        plotitem.axes['right']['item'] = caxis
        plotitem.layout.addItem(caxis, 2, 2)




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

    def experimentOpen(self):
        """
        This function will be called by the CCD window when
        the experiment is opened, after the experimental
        settings are populated
        :return:
        """
        pass

    def experimentClose(self):
        """
        This will be called when the experiment is closed
        ( when being changed to another experiment)
        :return:
        """
        pass

    @staticmethod
    def __IMAGE_COLLECTION_METHODS(): pass

    def takeImage(self, isBackground = False):
        """
        This function is called to set up a camera exposure.
        Toggle ui elements, set up a waiting thread, start the progress bar.
        The waiting thread then calls a processing event afterwards,
        as determined by isBackground
        :param isBackground: Nominally, a bool for whether the image
            being taken is the background (true) or data image (false).
            Forward compatibility allows you to pass a callable
            (must have __call__) so other functions could be called
            e.g. lambda:None, if you don't want anything to happen,
                new functino for continuous work,
                a third type of image data (sample, reference, background for abs)
                etc.
        :return:
        """
        try:
            self.papa.saveSettings()
        except Exception as e:
            log.error("Error saving settings to file, {}".format(e))

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



        # Update exposure/gain if necesssary. Include appropriate
        # parsing of camera response to ensure things have been accepted
        if not np.isclose(float(self.ui.tEMCCDExp.value()), self.papa.CCD.cameraSettings["exposureTime"]):
            ret = self.papa.CCD.setExposure(float(self.ui.tEMCCDExp.text()))
            self.ui.tEMCCDExp.setText(str(self.papa.CCD.cameraSettings["exposureTime"]))
            if ret != 20002:
                log.error("Error setting exposure time! {}".format(self.papa.CCD.parseRetCode(ret)))
                MessageDialog(self, "Error setting exposure time! {}".format(self.papa.CCD.parseRetCode(ret)))
                return
        if not int(self.ui.tEMCCDGain.text()) == self.papa.CCD.cameraSettings["gain"]:
            ret = self.papa.CCD.setGain(int(self.ui.tEMCCDGain.text()))
            self.ui.tEMCCDGain.setText(str(self.papa.CCD.cameraSettings["gain"]))
            if ret != 20002:
                log.error("Error setting gain value! {}".format(self.papa.CCD.parseRetCode(ret)))
                MessageDialog(self, "Error setting gain value! {}".format(self.papa.CCD.parseRetCode(ret)))
                return


        # Turn off UI elements to prevent conflicts
        # For some reson, if you do this in the thread,
        # Qt complains about starting timers in threads.
        # I could not figure out the source of this error, so
        # I prevent it by putting it here
        self.exposureElapsedTimer = QtCore.QElapsedTimer()
        self.toggleUIElements(False)

        if self.hasFEL:
            self.runSettings["fieldStrength"] = []
            self.runSettings["fieldInt"] = []
            self.ui.tCCDFELPulses.setText("0")
            self.papa.oscWidget.startExposure()
            # Probably clearer/better to connect this to a function...
            # Need to ignore signal if things iddn't work
            self.papa.oscWidget.sigPulseCounted.connect(
                    lambda x: [self.ui.tCCDFELPulses.setText(str(x)) if x>=0 else 0])
        self.thDoExposure.start()

    def doExposure(self, postProcessing = lambda: True):
        """
        This function should be called when you want to handle taking an image
        It checks the exposure/gain, sets them if necessary. Sets up timing to wait for
        completion of the image, etc

        This thread WILL hang. Do not call from main thread

        :return: sets self.rawData to the image taken from the camera.
        """

        self.runSettings["progress"] = 0

        if not self.papa.ui.mFileTakeContinuous.isChecked():
            # don't spam the log
            log.debug("Beginning an exposure")
        self.papa.CCD.dllStartAcquisition()
        if self.hasFEL and not self.papa.oscWidget.settings["isScopePaused"] and not self.papa.ui.mFileTakeContinuous.isChecked():
            # Wait for an FEL pulse before we start counting, as determined by
            # the oscilloscope triggering.
            #
            # This feature is intended to synchronize better with the camera
            # exposure when it is also triggered by the FEL.
            waitForPulseLoop = QtCore.QEventLoop()
            self.papa.oscWidget.sigOscDataCollected.connect(waitForPulseLoop.exit)
            waitForPulseLoop.exec_()

        self.runSettings["exposing"] = True

        if not self.papa.ui.mFileTakeContinuous.isChecked():
            self.sigStartTimer.emit()
        ret = self.papa.CCD.dllWaitForAcquisition()
        log.debug("Finished Waiting for Acquisition")
        self.runSettings["exposing"] = False
        if self.hasFEL:
            self.papa.oscWidget.stopExposure()
        self.sigMakeGui.emit(self.updateProgressBar, None)
        if self.hasFEL and not self.papa.ui.mFileTakeContinuous.isChecked():
            try:
                self.elWaitForOsc.exit()
            except:
                log.debug("Error exiting eventLoop waiting for pulses")
        if ret != 20002:
            log.debug("Acquisition not completed, Ret = {}".format(ret))
            self.sigMakeGui.emit(self.toggleUIElements, (True, ))
            return


        ret = self.papa.CCD.getImage()
        log.debug("Retrieved image from camera")
        # getImage will return the camera return value if it is not
        # 20002, otherwise it will return a np.array of the data
        # Thus, if the return is an int, it must have failed the return
        if isinstance(ret, int):
            self.sigMakeGui.emit(self.toggleUIElements, (True, ))
            # If 20024==nonew
            if ret == 20024:
                log.debug("No new data for image acquisition (Acquisition aborted?)")
            else:
                self.sigMakeGui.emit(MessageDialog, (self, "Invalid Image return! {}".format(ret)))
                log.warning("Invalid getImage return {}".format(ret))
            return
        self.rawData = ret
        postProcessing()

    def abortAcquisition(self):
        ret = self.papa.CCD.dllAbortAcquisition()
        log.debug("Abort acq return val: {}".format(ret))

    def startProgressBar(self):
        # things are breaking if the exposure time is too short
        # I'm pretty sure it's because I didn't do things intelligently,
        # but I think this is an edge case which doesn't have to work,
        # but certainly shouldn't crash the software like it does
        if self.papa.CCD.cameraSettings["exposureTime"]<=1:
            return

        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Waiting exposure")
        self.exposureElapsedTimer.start()

        self.progressTimer.timeout.connect(self.updateProgressBar)
        self.progressTimer.setInterval(self.papa.CCD.cameraSettings["exposureTime"]*10)
        self.progressTimer.setSingleShot(True)
        self.progressTimer.start()

    def updateProgressBar(self):
        # Weird asynchronicity can cause bizarre behavior
        # Make sure the timer isn't running, if it is, stop it
        if self.progressTimer.isActive():
            self.sigMakeGui.emit(self.progressTimer.stop, None)
            # self.progressTimer.stop()
        try:
            self.progressTimer.timeout.disconnect(self.updateProgressBar)
        except TypeError as e:
            pass
        # sometimes, this is slow enough to be unsynchronized with
        # the main thread, and image collection/processing
        # finishes before this. This will cause the
        # "Done" progress bar text to be replaced with
        # "Reading data". It doesn't matter, but Hunter
        # seems to think it's a problem, so stop letting
        # this happen.
        #
        # If the main thread finishes before this,
        # it will set 'exposing' to false, which we
        # will see here to set the progress bar directly to
        # 100 and not change the text
        if not self.runSettings["exposing"]:
            self.runSettings["progress"] = 100
            self.papa.updateElementSig.emit(self.ui.lCCDProg, "Reading Data")
            self.ui.pCCD.setValue(self.runSettings["progress"])
            return
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
                self.progressTimer.setInterval(newTime)
                self.progressTimer.timeout.connect(self.updateProgressBar)
                self.progressTimer.start()
            except:
                log.critical("Didn't update progress ")
        else:
            self.papa.updateElementSig.emit(self.ui.lCCDProg, "Reading Data")
            self.runSettings["exposing"] = False
            self.exposureElapsedTimer = None

    def startContinuous(self, value):
        # If not value, the box was being unchecked,
        # starting can ignore the call
        if value:

            self.runSettings["takingContinuous"] = True
            # Add infinite lines for ease in aligning
            self.ui.gCCDImage.view.addItem(self.ilOnep1)
            self.ui.gCCDImage.view.addItem(self.ilTwop1)
            self.ui.gCCDBin.plotItem.addItem(self.ilOnep2)
            self.ui.gCCDBin.plotItem.addItem(self.ilTwop2)

            # There's some weird, hard to track bug where occasionally,
            # if you're taking continuous, and you switch tabs and
            # then turn it on and off (or something like that. It seems
            # to be related to toggling it when you're not on the
            # data collection window), the plots would freeze, and would
            # require a resize (movign splitters, resizing window) to redraw
            # properly.
            #
            # First attempt, here, is to just turn off other tabs so that
            # you can never toggle collection when in another tab
            # Another fix could be looking into forcing a redraw of the plots
            # after updating data, (or calling whatever is called when a
            # widget gets a resize), though I don't konw how expensive it would
            # be to call a redraw for every single image.
            #
            # Note also that the bug is hard to find because it doesn't seem to
            # appear on faster-running computers (better ram? faster cpu? details
            # unclear)
            for i in range(self.papa.ui.tabWidget.count()):
                if i == self.papa.ui.tabWidget.indexOf(self.papa.getCurExp()): continue
                self.papa.ui.tabWidget.setTabEnabled(i, False)
            # Take an image and have the thread call the continuous collection loop
            # Done this way so that it's working off the same thread
            # that data collection would normally be performed on
            self.takeImage(isBackground = self.takeContinuousLoop)

    def takeContinuousLoop(self):
        while self.papa.ui.mFileTakeContinuous.isChecked():
            self.doExposure()
            # Update from the image that was taken in the first call
            # when starting the loop
            self.sigUpdateGraphs.emit(self.updateSignalImage, self.rawData)
            # create the object and clean it up
            image = EMCCD_image(self.rawData,
                                "", "", "", self.genEquipmentDict())
            # Ignore CRR and just set the clean to raw for summing
            image.clean_array = image.raw_array
            image.make_spectrum()
            self.sigUpdateGraphs.emit(self.updateSpectrum, image.spectrum)
            # self.doExposure()
        # re-enable UI elements, remove alignment plots
        self.toggleUIElements(True)
        self.ui.gCCDImage.view.removeItem(self.ilOnep1)
        self.ui.gCCDImage.view.removeItem(self.ilTwop1)
        self.ui.gCCDBin.plotItem.removeItem(self.ilOnep2)
        self.ui.gCCDBin.plotItem.removeItem(self.ilTwop2)

        # re-enable the other tabs
        for i in range(self.papa.ui.tabWidget.count()):
            if i == self.papa.ui.tabWidget.indexOf(self.papa.getCurExp()): continue
            self.papa.ui.tabWidget.setTabEnabled(i, True)
        self.runSettings["takingContinuous"] = False


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
        if not self.papa.ui.mLivePlotsDisableRawPlots.isChecked():
            self.sigUpdateGraphs.emit(self.updateSignalImage, self.rawData)
        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Cleaning Data")

        self.curDataEMCCD = self.DataClass(self.rawData,
                                           str(self.papa.ui.tImageName.text()),
                                           str(self.ui.tCCDImageNum.value()+1),
                                           str(self.ui.tCCDComments.toPlainText()),
                                           self.genEquipmentDict())


        self.curDataEMCCD.make_spectrum()
        log.debug("Emitting image updates")
        # self.sigUpdateGraphs.emit(self.updateSignalImage, self.curDataEMCCD.raw_array)
        self.sigUpdateGraphs.emit(self.updateSpectrum, self.curDataEMCCD.spectrum)
        # Do we want to keep this image?
        if not self.confirmImage():
            log.debug("Image rejected")
            self.papa.updateElementSig.emit(self.ui.lCCDProg, "Done.")
            self.sigMakeGui.emit(self.toggleUIElements, (True, ))
            return

        try:
            log.debug("Saving CCD Image")
            self.curDataEMCCD.save_images(self.papa.settings["saveDir"])
            self.papa.sigUpdateStatusBar.emit("Saved Image: {}".format(self.ui.tCCDImageNum.value()+1))
            self.papa.updateElementSig.emit(self.ui.tCCDImageNum, self.ui.tCCDImageNum.value()+1)
        except Exception as e:
            self.papa.sigUpdateStatusBar.emit("Error saving image")
            log.critical("folder str: {}, filename: {}".format(
                self.papa.settings["saveDir"], self.curDataEMCCD.file_name
            ))
            log.warning("Error saving Data image, {}".format(e))

        if self.papa.ui.mFileDoCRR.isChecked():
            self.curDataEMCCD.cosmic_ray_removal()
        else:
            self.curDataEMCCD.clean_array = self.curDataEMCCD.raw_array

        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Finishing Up...")

        # self.analyzeSeries()
        self.addImageSequence()
        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Done.")
        self.sigUpdateGraphs.emit(self.updateSignalImage, self.prevDataEMCCD.imageSequence.getImages())
        self.sigMakeGui.emit(self.toggleUIElements, (True, ))

    def processBackground(self):
        # self.sigUpdateGraphs.emit(self.updateBackgroundImage, self.rawData)
        # return
        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Cleaning Data")

        self.curBackEMCCD = self.DataClass(self.rawData,
                                           str(self.papa.ui.tBackgroundName.text()),
                                           str(self.ui.tCCDBGNum.value()+1),
                                           str(self.ui.tCCDComments.toPlainText()),
                                           self.genEquipmentDict())

        log.debug("Saving background images")
        try:
            self.curBackEMCCD.save_images(self.papa.settings["saveDir"])
            self.papa.sigUpdateStatusBar.emit("Saved Background: {}".format(self.ui.tCCDBGNum.value()+1))
            # incrememnt the counter, but certainly after we're done with it
            self.papa.updateElementSig.emit(self.ui.tCCDBGNum, self.ui.tCCDBGNum.value()+1)
        except Exception as e:
            self.papa.sigUpdateStatusBar.emit("Error saving image")
            log.critical("folder str: {}, filename: {}".format(
                self.papa.settings["saveDir"], self.curBackEMCCD.file_name
            ))
            log.exception("Error saving background image, {}".format(e))

        if self.papa.ui.mFileDoCRR.isChecked():
            self.curBackEMCCD.cosmic_ray_removal()
        else:
            self.curBackEMCCD.clean_array = self.curBackEMCCD.raw_array
        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Finishing up...")

        log.debug("Adding backgorund sequence")
        self.addBackgroundSequence()

        log.debug("Emitting background update")
        self.sigUpdateGraphs.emit(self.updateBackgroundImage, self.prevBackEMCCD.imageSequence.getImages())
        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Done.")
        log.debug("Reenabling after background")
        self.sigMakeGui.emit(self.toggleUIElements, (True, ))

    def confirmImage(self):
        """
        Prompts the user to ensure the most recent image is acceptable.
        :return: Boolean of whether or not to accept.
        """
        self.eloopConfirmImage = QtCore.QEventLoop()


        # As mentioned in other places, you can't make gui elements
        # in non-main thread, so you need to use a signal to tell
        # the main thread to handle it. This function will make
        # the necessary ui element, and emit it as a signal
        # to be made elsewhere
        def makr():
            prompt = QtGui.QMessageBox(self)
            prompt.setText("Save most recent scan?")
            prompt.setStandardButtons(QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard)
            prompt.setEscapeButton(QtGui.QMessageBox.Discard)
            prompt.setDefaultButton(QtGui.QMessageBox.Save)
            prompt.setModal(False)
            prompt.setWindowModality(QtCore.Qt.NonModal)
            prompt.buttonClicked.connect(self.eloopConfirmImage.quit)
            prompt.show()
            return prompt

        # I want to get the box returned to this thread.
        # The probably cleaner way would be to have a class
        # attribute to hold it, but I just... I don't know
        #
        # I feel better being able to have these two functions
        # be able to talk without having to pull in a
        # class attribute which only serves this purpose.
        # Unfortunately, python doesn't do pass by reference, so
        #
        p = []
        self.sigMakeGui.emit(makr, p)

        # Need to have a waiting loop to wait for the
        # main thread to process the signal and make the
        # dialog box


        self.eloopConfirmImage.exec_()

        try:
            p = p[0]
        except IndexError:
            log.critical("Something is wrong with getting the reference to the"
                         "dialog box")
            return True

        return p.buttonRole(p.clickedButton())==QtGui.QMessageBox.AcceptRole
        # return True

    def genEquipmentDict(self):
        """
        The EMCCD class wants a specific dictionary of values. This function will return it
        :return:
        """
        s = dict()
        s["date"] = time.strftime('%x')
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
        s["spec_step"] = str(self.ui.tSpectrumStep.text())
        s["ccd_image_settings"] = self.papa.CCD.cameraSettings["imageSettings"]
        if self.hasFEL:
            # s["fel_power"] = str(self.ui.tCCDFELP.text())
            # s["fel_reprate"] = str(self.ui.tCCDFELRR.text())
            # s["fel_lambda"] = str(self.ui.tCCDFELFreq.text())
            # s["fel_pol"] = str(self.ui.tCCDFELPol.text())
            # s["fel_pulses"] = int(self.ui.tCCDFELPulses.text()) if \
            #     str(self.ui.tCCDFELPulses.text()).strip() else 0
            try:
                s["fel_transmission"] = str(self.papa.motorDriverWid.ui.tCosCalc.text())
            except Exception as e:
                log.warning("Unable to grab wire grid transmission: {}".format(e))

            s.update(self.papa.oscWidget.getExposureResults())

        if self.hasNIR:
            s["nir_power"] = str(self.ui.tCCDNIRP.text())
            s["nir_lambda"] = str(self.ui.tCCDNIRwavelength.text())
            s["nir_pol"] = str(self.ui.tCCDNIRPol.text())

        # If the user has the series box as {<variable>} where variable is
        # any of the keys below, we want to replace it with the relavent value
        # Potentially unnecessary at this point...
        #
        # Also, need to have all possible keywords here as
        #     "{FELP}".format(GAIN=1)
        # does not return "{FELP}", as one would hope,
        # it just throws an error.
        #
        # Instead of adding a bunch of empty strings to the dict to
        # fill the role, use dict.get() so that a key error isn't thrown
        # when trying to access FEL/NIR only keys
        st = str(self.ui.tCCDSeries.text())
        st = st.format(**{k: s.get(v, -1.1) for k, v in seriesTags .items()})

        s["series"] = st
        return s

    @staticmethod
    def __SERIES_METHODS(): pass

    def analyzeSeries(self):
        #######################
        # Handling of series tag to add things up live
        #
        # Want it to save only the latest series, but also
        # the previous ones should be saved (hence why this is
        # after the saving is being done)
        #######################
        if str(self.ui.tCCDSeries.text())=="":
            # Undo if we don't have the series tag checked
            # or the label is empty
            self.prevDataEMCCD = None
            self.runSettings["seriesNo"] = 0
            self.ui.groupBox_Series.setTitle("Series")
            return

        groupBox = self.ui.groupBox_Series

        if (self.prevDataEMCCD is not None and # Is there something to add to?
                    self.prevDataEMCCD.equipment_dict["series"] == # With the same
                    self.curDataEMCCD.equipment_dict["series"] and # series tag?
                    self.prevDataEMCCD.equipment_dict["spec_step"] == # With the same
                    self.curDataEMCCD.equipment_dict["spec_step"] and # spectrum step?
                    self.curDataEMCCD.equipment_dict["series"] != "" and #which isn't empty
                    self.curDataEMCCD.file_name == self.prevDataEMCCD.file_name): #and from the same folder?
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
            groupBox.setTitle("Series ({})".format(self.runSettings["seriesNo"]))
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
            groupBox.setTitle("Series (1)")


        else:
            self.prevDataEMCCD = None
            self.runSettings["seriesNo"] = 0
            groupBox.setTitle("Series")
            log.debug("Made a new series where I didn't think I'd be")

    def undoSeries(self):
        """
        todo: 11/6 I think this is a broken function now
        :return:
        """
        log.critical("")
        log.critical("")
        log.critical("You actually called undoseries")
        log.critical("")
        log.critical("")
        log.debug("Removed two series together")
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
        self.ui.groupBox_Series.setTitle("Series ({})".format(self.runSettings["seriesNo"]))
        # but PLOT the normalized average
        self.prevDataEMCCD.spectrum[:,1]/=self.runSettings["seriesNo"]
        self.prevDataEMCCD.clean_array/=self.runSettings["seriesNo"]

        # Update the plots with this new data
        self.sigUpdateGraphs.emit(self.updateSignalImage, self.prevDataEMCCD.clean_array)
        self.sigUpdateGraphs.emit(self.updateSpectrum, self.prevDataEMCCD.spectrum)

    def addImageSequence(self):
        curBGtitle = str(self.ui.groupBox_37.title())
        # "It's easier to ask for forgiveness than
        #  for permission"
        try:
            self.prevDataEMCCD.addNewImage(
                self.curDataEMCCD
            )
            self.ui.groupBox_37.setTitle(
                curBGtitle.split('(')[0] + "({}*)".format(
                    self.prevDataEMCCD.imageSequence.numImages()
                )
            )
        except (AttributeError, ValueError):
            self.prevDataEMCCD = None
        if self.prevDataEMCCD is None:
            self.prevDataEMCCD = copy.deepcopy(self.curDataEMCCD)
            self.ui.groupBox_37.setTitle(
                curBGtitle.split('(')[0] + '(1*)'
            )
            self.prevDataEMCCD.setAsSequence()

    def addBackgroundSequence(self):
        curBGtitle = str(self.ui.groupBox_38.title())
        try:
            self.prevBackEMCCD.addNewImage(
                self.curBackEMCCD
            )
            self.ui.groupBox_38.setTitle(
                curBGtitle.split('(')[0] + "({}*)".format(
                    self.prevBackEMCCD.imageSequence.numImages()
                )
            )
        except (AttributeError, ValueError):
            self.prevBackEMCCD = None
        if self.prevBackEMCCD is None:
            self.prevBackEMCCD = copy.deepcopy(self.curBackEMCCD)
            self.ui.groupBox_38.setTitle(
                curBGtitle.split('(')[0] + '(1*)'
            )
            self.prevBackEMCCD.setAsSequence()
            self.prevBackEMCCD.imageSequence.ignoreNormFactors = True

    def removeImageSequence(self):
        """
        Remove the previous image sequence
        so future images will not get added to it
        :return:
        """
        self.prevDataEMCCD = None
        curBGtitle = str(self.ui.groupBox_37.title())
        curBGtitle = curBGtitle.split('(')[0]
        self.ui.groupBox_37.setTitle(
            curBGtitle
        )

    def removeBackgroundSequence(self):
        """
        Remove the previous image sequence
        so future images will not get added to it
        :return:
        """
        self.prevBackEMCCD = None
        curBGtitle = str(self.ui.groupBox_38.title())
        curBGtitle = curBGtitle.split('(')[0]
        self.ui.groupBox_38.setTitle(
            curBGtitle
        )

    def processImageSequence(self):
        d, std = self.confirmCosmicRemoval(self.prevDataEMCCD.imageSequence)
        if d is None:
            return

        try:
            self.prevDataEMCCD.equipment_dict["background_file"] = \
                self.curBackEMCCD.saveFileName
        except AttributeError:
            self.prevDataEMCCD.equipment_dict["background_file"] = "NoneTaken"

        d, sigpost, sigT = self.prevDataEMCCD.imageSequence.subtractImage(
            self.curBackEMCCD
        )
        self.prevDataEMCCD.clean_array = d
        self.updateSignalImage(d)
        self.prevDataEMCCD.std_array = sigpost

        try:
            self.prevDataEMCCD.save_images(
                folder_str=self.papa.settings["saveDir"],
                data = sigpost,
                fmt = '%f',
                postfix="_stdpost"
            )
            log.debug("Saved proccesed data image stdpost, {}".format(
                self.prevDataEMCCD.saveFileName
            ))
        except Exception as e:
            log.warn("error saving std file of processed data image stdpost. {}".format(
                e
            ))

        try:
            self.prevDataEMCCD.save_images(
                folder_str=self.papa.settings["saveDir"],
                data = sigT,
                fmt = '%f',
                postfix="_stdT"
            )
            log.debug("Saved proccesed data image stdT, {}".format(
                self.prevDataEMCCD.saveFileName
            ))
        except Exception as e:
            log.warn("error saving std file of processed data image stdT. {}".format(
                e
            ))

        try:
            self.prevDataEMCCD.save_images(
                folder_str=self.papa.settings["saveDir"],
                data = d,
                postfix="_seq",
                fmt='%f'
            )
            log.debug("Saved proccesed sequence image, {}".format(
                self.prevDataEMCCD.saveFileName
            ))
        except Exception as e:
            log.warn("error saving image file of processed sequence. {}".format(
                e
            ))

        # Now the fun part: Start to process it and deal with the
        # noise of the backgorund
        try:
            self.prevDataEMCCD.make_spectrum()
            oh = self.prevDataEMCCD.origin_import.splitlines()
            oh[1] += ",error"
            oh[2] += ",arb.u."
            oh.append(",{},".format(self.prevDataEMCCD.equipment_dict["series"]))
            oh = "\n".join(oh)

            self.prevDataEMCCD.save_spectrum(
                self.papa.settings["saveDir"],
                postfix = "seq",
                origin_header=oh
            )
        except Exception as e:
            log.warning("Exception trying to make/save the sequenced spectrum file\n\t\t"
                        "{}".format(e))

        self.curDataEMCCD = self.prevDataEMCCD
        curBGtitle = str(self.ui.groupBox_37.title()).replace('*', '')
        self.ui.groupBox_37.setTitle(
            curBGtitle
        )
        self.sigUpdateGraphs.emit(self.updateSpectrum, self.prevDataEMCCD.spectrum)
        self.prevDataEMCCD = None

    def processBackgroundSequence(self):
        d, std = self.confirmCosmicRemoval(self.prevBackEMCCD.imageSequence)
        if d is None:
            return


        self.updateBackgroundImage(d)
        self.prevBackEMCCD.clean_array = d
        self.prevBackEMCCD.std_array = std

        try:
            self.prevBackEMCCD.save_images(
                folder_str=self.papa.settings["saveDir"],
                data = std,
                fmt = '%f',
                postfix="_std"
            )
            log.debug("Saved proccesed background std, {}".format(
                self.prevBackEMCCD.saveFileName
            ))
        except Exception as e:
            log.warn("error saving std file of processed background. {}".format(
                e
            ))

        try:
            self.prevBackEMCCD.save_images(
                folder_str=self.papa.settings["saveDir"],
                data = d,
                postfix="_seq"
            )
            log.debug("Saved proccesed background image, {}".format(
                self.prevBackEMCCD.saveFileName
            ))
        except Exception as e:
            log.warn("error saving image file of processed background. {}".format(
                e
            ))

        self.curBackEMCCD = self.prevBackEMCCD
        curBGtitle = str(self.ui.groupBox_38.title()).replace('*', '')
        self.ui.groupBox_38.setTitle(
            curBGtitle
        )

        self.prevBackEMCCD = None

    def confirmCosmicRemoval(self, imSeq):
        """

        :param dataObject:
        :type dataObject: EMCCD_image
        :return:
        """
        mod = QtGui.QApplication.keyboardModifiers()
        debug = mod==QtCore.Qt.ShiftModifier
        ok = False
        while not ok:
            d, std = imSeq.removeCosmics(
                debug=debug, **self.crrSettings
            )
            if not debug: break
            prompt = QtGui.QMessageBox(self)
            prompt.setText("Acceptable Cosmic Removal?")
            prompt.setStandardButtons(
                QtGui.QMessageBox.Yes |QtGui.QMessageBox.No
            )
            prompt.setDefaultButton(QtGui.QMessageBox.Yes)
            prompt.setWindowModality(QtCore.Qt.WindowModal)
            response = prompt.exec_()

            # Have the garbage collector clear the windows
            imSeq.winList = []
            if response == QtGui.QMessageBox.Yes:
                ok = True
                break

            newRat1, dialogOk1 = QtGui.QInputDialog.getDouble(
                self, "New CRR Settings", "Ratio",
                self.crrSettings["ratio"], decimals=2
            )
            if not dialogOk1:
                imSeq._cleanImages = None
                return None, None
            newRat2, dialogOk2 = QtGui.QInputDialog.getDouble(
                self, "New CRR Settings", "Noise Ratio",
                self.crrSettings["noisecoeff"], decimals=2
            )
            if not dialogOk2:
                imSeq._cleanImages = None
                return None, None
            self.crrSettings["ratio"] = newRat1
            self.crrSettings["noisecoeff"] = newRat2
        return d, std

    def removeCurrentSeries(self):
        """
        Sometimes you mess up and took something with series tags
        that you didn't want taken. This will reset self.prevdata to
        None so that none ofthe things put into the series up to now
        will be added to the next ones.
        :return:
        """
        self.prevDataEMCCD = None
        self.runSettings["seriesNo"] = 0
        self.ui.groupBox_Series.setTitle("Series")

    def setCurrentSeries(self):
        """
        Maybe you forgot to check the "Do Series" button.
        Maybe you forgot to put the series tag in properly.
        Maybe you put in the wrong series tag
            (fix it, call removeCurrentSeries followed by this one)
        Setting the series after the fact may have some much helpful
        after-the-fact uses.
        :return:
        """
        self.prevDataEMCCD = copy.deepcopy(self.curDataEMCCD)
        self.prevDataEMCCD.file_no += "seriesed"
        self.runSettings["seriesNo"] = 1
        self.ui.groupBox_Series.setTitle("Series (1)")

    @staticmethod
    def __RELOADING_FILES(): pass
    def reloadBackgroundFiles(self):
        files = QtGui.QFileDialog.getOpenFileNames(
            self, "Choose background files",
            os.path.join(self.papa.settings["saveDir"], "Images")
        )
        files = [str(i) for i in files]
        files = [i for i in files if '.txt' in i]
        if not files:
            return

        print [i for i in files]
        if len(files) == 2 and any(['seq' in os.path.basename(ii) for ii in files]):
            self.reloadFullSequenceBackground(files)
        else:
            self.reloadPartialSequenceBackground(files)

    def reloadFullSequenceBackground(self, files):
        log.debug("Loading background sequence files...")
        seqFile = [ii for ii in files if 'seq' in os.path.basename(ii)][0]
        stdFile = [ii for ii in files if 'std' in os.path.basename(ii)][0]
        bg = loadImageFile(seqFile, cls=self.DataClass)
        log.debug("Loaded background sequence file")
        std, _ = loadImageFile(stdFile)

        log.debug("Loaded background std file")
        bg.std_array = std
        self.updateBackgroundImage(bg.clean_array)
        self.curBackEMCCD = bg
        self.prevBackEMCCD = None
        lenBG = bg.equipment_dict["noImages"]

        curBGtitle = str(self.ui.groupBox_38.title())
        curBGtitle = curBGtitle.split('(')[0] + "({})".format(
                    lenBG)
        self.ui.groupBox_38.setTitle(
            curBGtitle
        )

    def reloadPartialSequenceBackground(self, files):
        self.prevBackEMCCD = None
        bgs = [loadImageFile(ii, self.DataClass) for ii in files]
        bgs = sorted(bgs, key=lambda x:x.equipment_dict["fileno"])
        for bg in bgs:
            self.curBackEMCCD = bg
            self.addBackgroundSequence()
        # update images
        self.sigUpdateGraphs.emit(self.updateBackgroundImage, self.prevBackEMCCD.imageSequence.getImages())

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
        self.ui.tEMCCDExp.setEnabled(enabled)
        self.ui.tEMCCDGain.setEnabled(enabled)

    def updateSignalImage(self, data = None):
        if data.ndim == 3:
            # Need to transpose the second two axes for the
            # proper alignment.
            self.ui.gCCDImage.setImage(data, autoLevels=not self.papa.ui.mLivePlotsDisableHistogramAutoscale.isChecked(),
                                      autoHistogramRange=True,
                                      autoRange = False)
            # set it to the last image
            self.ui.gCCDImage.setCurrentIndex(data.shape[0])
        else:
            self.ui.gCCDImage.setImage(data, autoLevels=not self.papa.ui.mLivePlotsDisableHistogramAutoscale.isChecked(),
                                      autoHistogramRange=True,
                                      autoRange = False)

        # Set right axis to display real pixel coordinates
        start=self.papa.CCD.cameraSettings["imageSettings"][4] #vstart
        stop=self.papa.CCD.cameraSettings["imageSettings"][5]  # vstop
        step=self.papa.CCD.cameraSettings["imageSettings"][1]
        realPix = np.arange(start=start,
                            stop=stop,
                            step=step)

        self.ui.gCCDImage.getView().getAxis('right').setDataSet(
            lambda pix: pix*step + start
        )

    def autoscaleSignalHistogram(self):
        data = self.pSigImage.image
        self.pSigHist.setLevels(data.min(), data.max())

    def updateBackgroundImage(self, data = None):
        if data.ndim == 3:
            # Need to transpose the second two axes for the
            # proper alignment.
            self.ui.gCCDBack.setImage(data, autoLevels=not self.papa.ui.mLivePlotsDisableHistogramAutoscale.isChecked(),
                                      autoHistogramRange=True,
                                      autoRange = False)
            self.ui.gCCDBack.setCurrentIndex(data.shape[0])
        else:
            self.ui.gCCDBack.setImage(data, autoLevels=not self.papa.ui.mLivePlotsDisableHistogramAutoscale.isChecked(),
                                      autoHistogramRange=True,
                                      autoRange = False)

    def updateSpectrum(self, data = None):
        self.pSpec.setData(data[:,0], data[:,1])
        self.ui.gCCDBin.plotItem.getAxis('top').setDataSet(data[:,0])
        # self.ui.gCCDBin.plotItem.getAxis('top').setTicks([
        #     [i for i in zip(data[::10,0], np.arange(len(data[::10,0])))],
        #     []
        # ])

    def parseNIRL(self):
        """
        We want wavelength, but sometimes we're working with wavenumber
        It'd be nice to do the calculation in the software
        :return:
        """
        val = self.ui.tCCDNIRwavelength.value()
        if val>1500:
            self.ui.tCCDNIRwavelength.setText("{:.3f}".format(10000000./val))

    # def updateImageNumbers(self, isIm = True):
    #     """
    #     :param sender: flag for who sent
    #     :return:
    #     allow the user to update the image number counters
    #     """
    #     if isIm:
    #         self.papa.settings["igNumber"] = int(self.ui.tCCDImageNum.text())+1
    #     else:
    #         self.papa.settings["bgNumber"] = int(self.ui.tCCDBGNum.text())+1

    def createGuiElement(self, fnc, args=None):
        """
        You can't make a GUI element from a worker thread, only from the
        main gui thread. This means that if you want to make a GUI element
        (e.g. a dialog box) while in another thread, you need to tell
        the main thread to do it, which is done through self.sigMakeGui.emit()
        and sent here. Done in a very general way that a function is passed
        to be called with given arguments. The return value is emitted in
        sigKillEventLoop as the worker thread may want to wait for the
        response before continuing.

        :param fnc: a function to be called
        :param args: a tuple of functions to pass
            (signals can't do arbitrary numbers via *args, I don't think)
        :return: emits return value through sigKillEventLoop.
            ( terminating a QEventLoop.exec_() with a value will
              cause the loop to return that value
                (Note: May cause issue with non-integer returns?)
        """
        try:
            if args is None:
                ret = fnc()
            else:
                ret = fnc(*args)
            if isinstance(args, list) and not args:
                args.append(ret)

            self.sigKillEventLoop.emit(ret)
        except Exception as e:
            log.critical("Error creating gui element.")
            log.critical("\t{},args:{}, error: {}".format(fnc, args, e))

class BaseHSGWid(BaseExpWidget):
    hasNIR = True
    hasFEL = True

    DataClass = HSG_image
    name = 'HSG'
    def __init__(self, parent = None, UI = None):
        if UI is None:
            UI = Ui_HSG
        super(BaseHSGWid, self).__init__(parent, UI)
        self.initUI()


    def initUI(self):
        # Set up the things for the slider which tells you
        # what sideband you're on
        self.ilSpec = pg.InfiniteLine(movable=True,
                                     pen=pg.mkPen(width=2, color='g'))
        self.ilSpec.sigPositionChanged.connect(self.updateSBfromLine)
        self.ui.gCCDBin.addItem(self.ilSpec)
        self.ui.tCCDSidebandNumber.textAccepted.connect(self.updateSBfromValue)

        self.freqInfoText = pg.TextItem('', color=(0,0,0))
        self.freqInfoText.setPos(0,0)
        self.freqInfoText.setFont(QtGui.QFont("", 15))
        self.ui.gCCDBin.addItem(self.freqInfoText)
        self.ui.gCCDBin.sigRangeChanged.connect(self.updateFreqText)

    def updateSBfromLine(self):
        try:
            wn = 10000000./self.ui.tCCDNIRwavelength.value()
            wanted = 10000000./self.ilSpec.value()
            sbn = (wanted-wn)/self.papa.oscWidget.ui.tFELFreq.value()
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
            wanted = wn + self.ui.tCCDSidebandNumber.value()*self.papa.oscWidget.ui.tFELFreq.value()
            wanted = 10000000./wanted
            # Need to disconnect/reconnect here, otherwise they call each other infinitely
            self.ilSpec.sigPositionChanged.disconnect(self.updateSBfromLine)
            self.ilSpec.setValue(wanted)
            self.ilSpec.sigPositionChanged.connect(self.updateSBfromLine)
        except Exception as e:
            log.warning("Could not update SB line from inputted value, {}".format(e))

    def updateFreqText(self, pw, range):
        self.freqInfoText.setPos(range[0][0], range[1][1])

    def processImage(self):
        super(BaseHSGWid, self).processImage()
        # need to emit cause thsi is called
        # self.sigMakeGui.emit(self.freqInfoText.setText, ('', ))
        self.sigMakeGui.emit(self.calculateFrequencies, ())

    def processImageSequence(self):
        super(BaseHSGWid, self).processImageSequence()
        try:
            spec = hsg.HighSidebandCCD(str(self.curDataEMCCD.spectrumFileName))
            spec.guess_sidebands()
            spec.fit_sidebands()
        except Exception as e:
            log.exception("Bad fitting {}".format(e))
            return
        # fit the positions up to the last two (generally noisy points
        # which throw off the fits
        p = np.polyfit(spec.sb_results[:-2,0], spec.sb_results[:-2,1], deg=1)
        fel = p[0]*8065.54429 # get fel freq in cm-1
        nir = p[1] * 8065.54429# get nir freq in cm-1

        g = '#00FF00'
        r = '#FF0000'

        felcolor = g
        nircolor = g
        if np.abs(1e7/self.ui.tCCDNIRwavelength.value() - nir) > 8:
            nircolor = r
        if np.abs(self.papa.oscWidget.ui.tFELFreq.value()-fel)>0.1:
            felcolor = r
        self.freqInfoText.setHtml(
            "<font color={}>FEL: {:.1f} GHz ({:.2f} cm<sup>-1</sup>)</font><br>".format(
                felcolor, fel*29.97925, fel
            )+\
            "<font color={}>NIR: {:.3f} nm ({:.1f} cm<sup>-1</sup>)</font>".format(
                nircolor, 1e7/nir, nir
            )
        )

    def calculateFrequencies(self):
        try:
            spec = hsg.HighSidebandCCD(self.curDataEMCCD.spectrum,
                                       self.curDataEMCCD.equipment_dict)
            spec.guess_sidebands()
            spec.fit_sidebands()

            nir, fel = spec.infer_frequencies(nir_units="wavenumber",
                                              thz_units="wavenumber")
        except Exception as e:
            log.exception("Bad fitting {}".format(e))
            return

        g = '#00FF00'
        r = '#FF0000'

        felcolor = g
        nircolor = g
        if np.abs(1e7/self.ui.tCCDNIRwavelength.value() - nir) > 8:
            nircolor = r
        if np.abs(self.papa.oscWidget.ui.tFELFreq.value()-fel)>0.1:
            felcolor = r
        self.freqInfoText.setHtml(
            "<font color={}>FEL: {:.1f} GHz ({:.2f} cm<sup>-1</sup>)</font><br>".format(
                felcolor, fel*29.97925, fel
            )+\
            "<font color={}>NIR: {:.3f} nm ({:.1f} cm<sup>-1</sup>)</font>".format(
                nircolor, 1e7/nir, nir
            )
        )


class HSGImageWid(BaseHSGWid):
    pass

class HSGFVBWid(BaseHSGWid):
    DataClass = HSG_FVB_image
    def __init__(self, parent = None, UI = None):
        super(HSGFVBWid, self).__init__(parent, UI)
        # self.seriesed_data = self.DataClass()

    def analyzeSeries(self):
        if str(self.ui.tCCDSeries.text())=="":
            # Undo if we don't have the series tag checked
            # or the label is empty
            self.prevDataEMCCD = None
            self.runSettings["seriesNo"] = 0
            self.ui.groupBox_Series.setTitle("Series")
            return
        groupBox = self.ui.groupBox_Series

        if (self.prevDataEMCCD is not None and # Is there something to add to?
                    self.prevDataEMCCD.equipment_dict["series"] == # With the same
                    self.curDataEMCCD.equipment_dict["series"] and # series tag?
                    self.prevDataEMCCD.equipment_dict["spec_step"] == # With the same
                    self.curDataEMCCD.equipment_dict["spec_step"] and # spectrum step?
                    self.curDataEMCCD.equipment_dict["series"] != "" and #which isn't empty
                    self.curDataEMCCD.file_name == self.prevDataEMCCD.file_name): #and from the same folder?

            self.prevDataEMCCD.addSpectrum(self.curDataEMCCD)
            self.prevDataEMCCD.make_spectrum()

            try:
                self.prevDataEMCCD.save_spectrum(self.papa.settings["saveDir"])
            except IOError as e:
                self.papa.sigUpdateStatusBar.emit("Error Saving Series")
                log.exception("Error saving series data, {}".format(e))
            try:
                self.prevDataEMCCD.save_images(self.papa.settings["saveDir"])
            except IOError as e:
                self.papa.sigUpdateStatusBar.emit("Error Saving Image")
                log.exception("Error saving FVB series image, {}".format(e))


            self.runSettings["seriesNo"] += 1
            groupBox.setTitle("Series ({})".format(self.runSettings["seriesNo"]))
        elif str(self.ui.tCCDSeries.text()) != "":
            self.prevDataEMCCD = copy.deepcopy(self.curDataEMCCD)
            self.prevDataEMCCD.initializeSeries()
            self.runSettings["seriesNo"] = 1
            groupBox.setTitle("Series (1)")


        # Update the plots with this new data
        self.sigUpdateGraphs.emit(self.updateSignalImage, self.prevDataEMCCD.raw_array)
        self.sigUpdateGraphs.emit(self.updateSpectrum, self.prevDataEMCCD.spectrum)

    def doCosmicRemoval(self, b):
        if not b: return
        self.papa.ui.mFileDoCRR.setChecked(False)
        if self.prevDataEMCCD is None:
            log.error("Unable to remove cosmics without a series")
            return
        if self.prevDataEMCCD.raw_array.shape[0] <= 1:
            log.error("Unable to remove cosmics with only one exposure")
            return
        if self.prevDataEMCCD.raw_array.shape[0] <= 3:
            log.warn("CRR is not tested with less than 4 exposures")

        offset = 0
        medianRatio = 1.
        noiseCoeff = 5.

        self.prevDataEMCCD.cosmic_ray_removal(
            offset = offset,
            medianRatio = medianRatio,
            noiseCoeff = noiseCoeff
        )

        self.prevDataEMCCD.make_spectrum()
        """
        DEBUGGING:
        DO NOT SAVE THEM AFTER DOING CRR
        try:
            self.prevDataEMCCD.save_spectrum(self.papa.settings["saveDir"])
        except IOError as e:
            self.papa.sigUpdateStatusBar.emit("Error Saving Series")
            log.debug("Error saving series data, {}".format(e))
        try:
            self.prevDataEMCCD.save_images(self.papa.settings["saveDir"])
        except IOError as e:
            self.papa.sigUpdateStatusBar.emit("Error Saving Image")
            log.debug("Error saving Image data, {}".format(e))
        """
        self.sigUpdateGraphs.emit(self.updateSignalImage, self.prevDataEMCCD.clean_array)
        self.sigUpdateGraphs.emit(self.updateSpectrum, self.prevDataEMCCD.spectrum)


    def experimentOpen(self):
        self.parentDoCRR = self.papa.ui.mFileDoCRR.isChecked()
        self.papa.ui.mFileDoCRR.setChecked(False)
        self.papa.ui.mFileDoCRR.triggered[bool].connect(self.doCosmicRemoval)


    def experimentClose(self):
        self.papa.ui.mFileDoCRR.setChecked(self.parentDoCRR)


class HSGPCWid(BaseHSGWid):
    pass

class AbsWid(BaseExpWidget):
    hasNIR = False
    hasFEL = False

    DataClass = Abs_image
    name = 'Absorbance'
    def __init__(self, parent = None, UI = None):
        # Want a UI parameter because this class
        # gets extended for two color (FEL/LED)
        # abs experiments, and I need to pass
        if UI is None:
            UI = Ui_Abs
        super(AbsWid, self).__init__(parent, UI)
        self.initUI()
        self.curRefEMCCD = None
        self.prevRefEMCCD = None
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

        self.ui.bProcessReferenceSequence.clicked.connect(self.processReferenceSequence)

    def experimentOpen(self):
        self.ui.tCCDRefNum.setText(str(self.papa.settings["rfNumber"]))
        self.papa.ui.mLoadReferences.setVisible(True)

    def experimentClose(self):
        self.papa.ui.mLoadReferences.setVisible(False)

    def takeReference(self):
        self.takeImage(isBackground = self.processReference)

    def processImage(self):
        super(AbsWid, self).processImage()
        # update the abs spectra if necessary
        if self.curRefEMCCD is None or not self.curRefEMCCD==self.curDataEMCCD:
            return
        else:
            try:
                self.curAbsEMCCD = (self.curDataEMCCD-self.curBackEMCCD)/self.curRefEMCCD
                self.sigUpdateGraphs.emit(self.updateSpectrum, self.curAbsEMCCD)
            except Exception as e:
                log.warning("Error updating abs spectrum {}".format(e))

    def reloadReferenceFiles(self):
        files = QtGui.QFileDialog.getOpenFileNames(
            self, "Choose reference files",
            os.path.join(self.papa.settings["saveDir"], "Images")
        )
        files = [str(i) for i in files]
        files = [i for i in files if '.txt' in i]
        if not files:
            return

        print [i for i in files]
        if len(files) == 2 and any(['seq' in os.path.basename(ii) for ii in files]):
            self.reloadFullSequenceReference(files)
        else:
            self.reloadPartialSequenceReference(files)

    def reloadFullSequenceReference(self, files):
        log.debug("Loading reference sequence files...")
        seqFile = [ii for ii in files if 'seq' in os.path.basename(ii)][0]
        stdFile = [ii for ii in files if 'std' in os.path.basename(ii)][0]
        ref = loadImageFile(seqFile, cls=self.DataClass)
        log.debug("Loaded reference sequence file")
        std, _ = loadImageFile(stdFile)

        log.debug("Loaded reference std file")
        ref.std_array = std
        self.curRefEMCCD = ref
        self.prevRefEMCCD = None
        lenref = ref.equipment_dict["noImages"]

        curReftitle = str(self.ui.groupBox.title())
        curReftitle = curReftitle.split('(')[0] + "({})".format(
                    lenref)
        self.ui.groupBox.setTitle(
            curReftitle
        )
        self.sigUpdateGraphs.emit(self.updateSpectrum, self.curRefEMCCD)
        self.sigUpdateGraphs.emit(self.updateSignalImage, self.curRefEMCCD.imageSequence.getImages())

    def reloadPartialSequenceReference(self, files):
        self.prevRefEMCCD = None
        refs = [loadImageFile(ii, self.DataClass) for ii in files]
        refs = sorted(refs, key=lambda x:x.equipment_dict["fileno"])
        for ref in refs:
            self.curRefEMCCD = ref
            self.addReferenceSequence()
        # update images
        self.sigUpdateGraphs.emit(self.updateSpectrum, self.curRefEMCCD)
        self.sigUpdateGraphs.emit(self.updateSignalImage, self.prevRefEMCCD.imageSequence.getImages())

    def processImageSequence(self):
        super(AbsWid, self).processImageSequence()
        if self.curRefEMCCD is None or not self.curRefEMCCD==self.curDataEMCCD:
            self.papa.sigUpdateStatusBar.emit("Please take a reference with the same settings")
            log.warning("Please take a reference with the same settings")
            return
        else:
            self.curDataEMCCD.equipment_dict["reference_file"] = self.curRefEMCCD.getFileName()
            self.curAbsEMCCD = self.curDataEMCCD/self.curRefEMCCD
            self.curAbsEMCCD.origin_import = \
                '\nWavelength,Raw Blank,Raw Trans,Abs\nnm,arb.u.,arb.u.,bels'
            try:
                self.curAbsEMCCD.save_spectrum(folder_str=self.papa.settings["saveDir"], prefix="abs_")
            except Exception as e:
                self.papa.sigUpdateStatusBar.emit("Error saving Absorbance")
                log.warning("Error saving Absorbance Spectrum, {}".format(e))
            self.sigUpdateGraphs.emit(self.updateSpectrum, self.curAbsEMCCD)



    def processReference(self):
        if not self.papa.ui.mLivePlotsDisableRawPlots.isChecked():
            self.sigUpdateGraphs.emit(self.updateSignalImage, self.rawData)
        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Cleaning Data")

        self.curRefEMCCD = self.DataClass(self.rawData,
                                           str(self.papa.ui.tImageName.text()),
                                           str(self.ui.tCCDRefNum.value()+1),
                                           str(self.ui.tCCDComments.toPlainText()),
                                           self.genEquipmentDict())

        self.curRefEMCCD.make_spectrum()
        log.debug("Emitting image updates")
        # self.sigUpdateGraphs.emit(self.updateSignalImage, self.curDataEMCCD.raw_array)
        self.sigUpdateGraphs.emit(self.updateSpectrum, self.curRefEMCCD)
        # Do we want to keep this image?
        if not self.confirmImage():
            log.debug("Image rejected")
            self.papa.updateElementSig.emit(self.ui.lCCDProg, "Done.")
            self.sigMakeGui.emit(self.toggleUIElements, (True, ))
            return

        try:
            log.debug("Saving CCD Ref Image")
            self.curRefEMCCD.save_images(self.papa.settings["saveDir"], prefix='absRef_')
            self.papa.sigUpdateStatusBar.emit("Saved Image: {}".format(self.ui.tCCDRefNum.value()+1))
            self.papa.updateElementSig.emit(self.ui.tCCDRefNum, self.ui.tCCDRefNum.value()+1)
        except Exception as e:
            self.papa.sigUpdateStatusBar.emit("Error saving image")
            log.critical("folder str: {}, filename: {}".format(
                self.papa.settings["saveDir"], self.curRefEMCCD.file_name
            ))
            log.warning("Error saving ref Data image, {}".format(e))

        if self.papa.ui.mFileDoCRR.isChecked():
            self.curRefEMCCD.cosmic_ray_removal()
        else:
            self.curRefEMCCD.clean_array = self.curRefEMCCD.raw_array

        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Finishing Up...")

        self.addReferenceSequence()
        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Done.")
        self.sigUpdateGraphs.emit(self.updateSignalImage, self.prevRefEMCCD.imageSequence.getImages())
        self.sigMakeGui.emit(self.toggleUIElements, (True, ))

    def addReferenceSequence(self):
        curBGtitle = str(self.ui.groupBox.title())
        # "It's easier to ask for forgiveness than
        #  for permission"
        try:
            self.prevRefEMCCD.addNewImage(
                self.curRefEMCCD
            )
            self.ui.groupBox.setTitle(
                curBGtitle.split('(')[0] + "({}*)".format(
                    self.prevRefEMCCD.imageSequence.numImages()
                )
            )
        except (AttributeError, ValueError):
            self.prevRefEMCCD = None
        if self.prevRefEMCCD is None:
            self.prevRefEMCCD = copy.deepcopy(self.curRefEMCCD)
            self.ui.groupBox.setTitle(
                curBGtitle.split('(')[0] + '(1*)'
            )
            self.prevRefEMCCD.setAsSequence()

    def processReferenceSequence(self):
        d, std = self.confirmCosmicRemoval(self.prevRefEMCCD.imageSequence)
        if d is None:
            return

        try:
            self.prevRefEMCCD.equipment_dict["background_file"] = \
                self.curBackEMCCD.saveFileName
        except AttributeError:
            self.prevRefEMCCD.equipment_dict["background_file"] = "NoneTaken"
        d, sigpost, sigT = self.prevRefEMCCD.imageSequence.subtractImage(
            self.curBackEMCCD
        )
        self.prevRefEMCCD.clean_array = d
        self.updateSignalImage(d)
        self.prevRefEMCCD.std_array = sigpost

        try:
            self.prevRefEMCCD.save_images(
                folder_str=self.papa.settings["saveDir"],
                prefix='absRef_',
                data = sigpost,
                fmt = '%f',
                postfix="_stdpost"
            )
            log.debug("Saved proccesed ref data image stdpost, {}".format(
                self.prevRefEMCCD.saveFileName
            ))
        except Exception as e:
            log.warn("error saving std file of processed ref data image stdpost. {}".format(
                e
            ))

        try:
            self.prevRefEMCCD.save_images(
                folder_str=self.papa.settings["saveDir"],
                prefix='absRef_',
                data = sigT,
                fmt = '%f',
                postfix="_stdT"
            )
            log.debug("Saved proccesed ref data image stdT, {}".format(
                self.prevRefEMCCD.saveFileName
            ))
        except Exception as e:
            log.warn("error saving std file of processed ref data image stdT. {}".format(
                e
            ))

        try:
            self.prevRefEMCCD.save_images(
                folder_str=self.papa.settings["saveDir"],
                prefix='absRef_',
                data = d,
                postfix="_seq"
            )
            log.debug("Saved proccesed ref sequence image, {}".format(
                self.prevRefEMCCD.saveFileName
            ))
        except Exception as e:
            log.warn("error saving image file of processed ref sequence. {}".format(
                e
            ))

        # Now the fun part: Start to process it and deal with the
        # noise of the backgorund
        try:
            self.prevRefEMCCD.make_spectrum()
            oh = self.prevRefEMCCD.origin_import.splitlines()
            oh[1] += ",error"
            oh[2] += ",arb.u."
            oh.append(",{},".format(self.prevRefEMCCD.equipment_dict["series"]))
            oh = "\n".join(oh)

            self.prevRefEMCCD.save_spectrum(
                self.papa.settings["saveDir"],
                prefix='absRef_',
                postfix = "seq",
                origin_header=oh
            )
        except Exception as e:
            log.warning("Exception trying to make/save the ref sequenced spectrum file,"
                        "{}".format(e))

        self.curRefEMCCD = self.prevRefEMCCD
        curBGtitle = str(self.ui.groupBox.title()).replace('*', '')
        self.ui.groupBox.setTitle(
            curBGtitle
        )
        self.sigUpdateGraphs.emit(self.updateSpectrum, self.curRefEMCCD)
        self.prevRefEMCCD = None

    def processReferenceOld(self):
        self.sigUpdateGraphs.emit(self.updateSignalImage, self.rawData)
        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Cleaning Data")

        self.curRefEMCCD = self.DataClass(self.rawData,
                                            str(self.papa.ui.tImageName.text()),
                                            str(self.ui.tCCDRefNum.value()+1),
                                            str(self.ui.tCCDComments.toPlainText()),
                                            self.genEquipmentDict())
        self.curRefEMCCD.origin_import = \
            '\nWavelength, Raw Blank\nnm,arb. u.'

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
        # self.curRefEMCCD.inspect_dark_regions()
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

    def updateGraphViews(self):
        self.pRawvb.setGeometry(self.ui.gCCDBin.plotItem.vb.sceneBoundingRect())
        self.pRawvb.linkedViewChanged(self.ui.gCCDBin.plotItem.vb,
                                      self.pRawvb.XAxis)

    def toggleUIElements(self, enabled = True):
        super(AbsWid, self).toggleUIElements(enabled)
        self.ui.bCCDReference.setEnabled(enabled)

    def updateSpectrum(self, data = None):
        title = "Transmission"
        # Need to use id() because we've overloaded __eq__ for the
        # data class to check for camera settings

        if id(data) == id(self.curAbsEMCCD):
            self.pSpec.setData(self.curAbsEMCCD.spectrum[:,0], self.curAbsEMCCD.spectrum[:,3])
            self.pRawBlank.setData(self.curAbsEMCCD.spectrum[:,0], self.curAbsEMCCD.spectrum[:,1])
            self.pRawTrans.setData(self.curAbsEMCCD.spectrum[:,0], self.curAbsEMCCD.spectrum[:,2])
            data = self.curAbsEMCCD.spectrum # for updating pixel axis on top of graph
        elif id(data)==id(self.curRefEMCCD):
            title = "Blank"
            data = self.curRefEMCCD.spectrum
            self.pRawBlank.setData(data[:,0], data[:,1])
            self.pSpec.setData([], [])
            self.pRawTrans.setData([], [])
            if self.ui.gCCDBin.plotItem.vb.state["autoRange"][0]:
                self.ui.gCCDBin.plotItem.setRange(
                    xRange=data[[0,-1],0]
                )
                self.ui.gCCDBin.plotItem.vb.enableAutoRange(x=True)
        else:
            self.pRawTrans.setData(data[:,0], data[:,1])
            if self.ui.gCCDBin.plotItem.vb.state["autoRange"][0]:
                self.ui.gCCDBin.plotItem.setRange(
                    xRange=data[[0,-1],0]
                )
                self.ui.gCCDBin.plotItem.vb.enableAutoRange(x=True)
            self.updateGraphViews()

        # set top axis to pixel number
        self.ui.gCCDBin.plotItem.getAxis('top').setDataSet(data[:,0])

        # super(AbsWid, self).updateSpectrum(data)
        # pi = self.ui.gCCDBin.getPlotItem()
        # pi.setTitle(title)

    def genEquipmentDict(self):
        s = super(AbsWid, self).genEquipmentDict()
        s["led_current"] = str(self.ui.tCCDLEDCurrent.text())
        s["led_temp"] = float(self.ui.tCCDLEDTemp.text())
        s["led_power"] = float(self.ui.tCCDLEDPower.text())
        return s

class TwoColorAbsWid(AbsWid):
    hasFEL = True
    name = 'Two Color Abs'

    def __init__(self, parent = None):
        super(TwoColorAbsWid, self).__init__(parent, Ui_TwoColorAbs)

class PLWid(BaseExpWidget):
    hasNIR = True
    hasFEL = False

    DataClass = PL_image
    name = 'PL'
    def __init__(self, parent = None):
        super(PLWid, self).__init__(parent, Ui_PL)

class AlignWid(BaseExpWidget):
    hasNIR = True
    hasFEL = False
    DataClass = EMCCD_image
    name = 'Vertical Alignment'
    def __init__(self, parent=None):
        super(AlignWid, self).__init__(parent, Ui_Alignment)
        self.ilOne = pg.InfiniteLine(pos=100, movable=True, pen='r')
        self.ilTwo = pg.InfiniteLine(pos=800, movable=True, pen='b')
        self.ilThree = pg.InfiniteLine(pos=1100, movable=True, pen='g')
        self.ui.gCCDImage.view.addItem(self.ilOne)
        self.ui.gCCDImage.view.addItem(self.ilTwo)
        self.ui.gCCDImage.view.addItem(self.ilThree)
        """
        todo: remvoet his
        self.p1.addItem(self.ilOne)
        self.p1.addItem(self.ilTwo)
        self.p1.addItem(self.ilThree)
        """
        self.ilOne.sigPositionChanged.connect(self.sumLines)
        self.ilTwo.sigPositionChanged.connect(self.sumLines)
        self.ilThree.sigPositionChanged.connect(self.sumLines)
        self.curveOne = self.ui.gCCDBin.plot(pen=pg.mkPen('r', width=3))
        self.curveTwo = self.ui.gCCDBin.plot(pen=pg.mkPen('b', width=3))
        self.curveThree = self.ui.gCCDBin.plot(pen=pg.mkPen('g', width=3))
        self.ui.tCCDSampleTemp.setText('2')



    def startContinuous(self, value):
        # If not value, the box was being unchecked,
        # starting can ignore the call
        if value:

            self.runSettings["takingContinuous"] = True

            for i in range(self.papa.ui.tabWidget.count()):
                 if i == self.papa.ui.tabWidget.indexOf(self.papa.getCurExp()): continue
                 self.papa.ui.tabWidget.setTabEnabled(i, False)
            # Take an image and have the thread call the continuous collection loop
            # Done this way so that it's working off the same thread
            # that data collection would normally be performed on
            self.takeImage(isBackground = self.takeContinuousLoop)

    def takeContinuousLoop(self):
        while self.papa.ui.mFileTakeContinuous.isChecked():
            self.doExposure()
            # Update from the image that was taken in the first call
            # when starting the loop
            self.sigUpdateGraphs.emit(self.updateSignalImage, self.rawData)
            # create the object and clean it up
            image = EMCCD_image(self.rawData,
                                "", "", "", self.genEquipmentDict())
            # Ignore CRR and just set the clean to raw for summing
            image.clean_array = image.raw_array
            self.curDataEMCCD = image
            self.sumLines()
        for i in range(self.papa.ui.tabWidget.count()):
             if i == self.papa.ui.tabWidget.indexOf(self.papa.getCurExp()): continue
             self.papa.ui.tabWidget.setTabEnabled(i, True)
        # re-enable UI elements, remove alignment plots
        self.toggleUIElements(True)


    def processImage(self):
        self.papa.updateElementSig.emit(self.ui.lCCDProg, "Cleaning Data")

        self.curDataEMCCD = self.DataClass(self.rawData,
                                            str(self.papa.ui.tImageName.text()),
                                            str(self.ui.tCCDImageNum.value()+1),
                                            str(self.ui.tCCDComments.toPlainText()),
                                            self.genEquipmentDict())

        self.curDataEMCCD.clean_array = self.curDataEMCCD.raw_array


        self.sigUpdateGraphs.emit(self.updateSignalImage, self.curDataEMCCD.clean_array)
        # self.sigUpdateGraphs.emit(self.updateSpectrum, self.curDataEMCCD.spectrum)
        self.sumLines()

        self.toggleUIElements(True)


    def updateSpectrumOne(self, data = None):
        self.curveOne.setData(data)

    def updateSpectrumTwo(self, data = None):
        self.curveTwo.setData(data)

    def updateSpectrumThree(self, data = None):
        self.curveThree.setData(data)


    def sumLines(self, line=None):
        if self.curDataEMCCD is None:
            return
        toDo = []
        if line is None:
            toDo = [1, 2, 3]
        elif line is self.ilOne:
            toDo = [1]
        elif line is self.ilTwo:
            toDo = [2]
        elif line is self.ilThree:
            toDo = [3]

        if 1 in toDo:
            pos = self.ilOne.value()
            data = self.sumData(pos)
            self.sigUpdateGraphs.emit(self.updateSpectrumOne, data)
        if 2 in toDo:
            pos = self.ilTwo.value()
            data = self.sumData(pos)
            self.sigUpdateGraphs.emit(self.updateSpectrumTwo, data)
        if 3 in toDo:
            pos = self.ilThree.value()
            data = self.sumData(pos)
            self.sigUpdateGraphs.emit(self.updateSpectrumThree, data)

    def sumData(self, pos):
        try:
            width = int(self.ui.tCCDSampleTemp.text())
        except ValueError:
            width = 1
        st = pos-width/2
        if st<0:
            st = 0
        en = pos + width/2
        if st == en:
            en +=1
        data = np.sum(self.curDataEMCCD.clean_array[st:en,:], axis=0)
        data = data.astype(float)
        data-=min(data)
        data/=max(data)
        return data



if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    ex = AbsWid()
    ex.show()
    sys.exit(app.exec_())