# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\FELLab\Documents\GitHub\EMCCD-psychic\UIs\PL.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_PL(object):
    def setupUi(self, PL):
        PL.setObjectName("PL")
        PL.resize(924, 751)
        self.verticalLayout = QtWidgets.QVBoxLayout(PL)
        self.verticalLayout.setObjectName("verticalLayout")
        self.splitterAll = QtWidgets.QSplitter(PL)
        self.splitterAll.setOrientation(QtCore.Qt.Vertical)
        self.splitterAll.setObjectName("splitterAll")
        self.splitterTop = QtWidgets.QSplitter(self.splitterAll)
        self.splitterTop.setOrientation(QtCore.Qt.Horizontal)
        self.splitterTop.setObjectName("splitterTop")
        self.tabWidget_3 = QtWidgets.QTabWidget(self.splitterTop)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget_3.sizePolicy().hasHeightForWidth())
        self.tabWidget_3.setSizePolicy(sizePolicy)
        self.tabWidget_3.setObjectName("tabWidget_3")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.tab_3)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.groupBox_42 = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_42.setFlat(True)
        self.groupBox_42.setCheckable(False)
        self.groupBox_42.setObjectName("groupBox_42")
        self.gridLayout_12 = QtWidgets.QGridLayout(self.groupBox_42)
        self.gridLayout_12.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_12.setSpacing(0)
        self.gridLayout_12.setObjectName("gridLayout_12")
        self.tSampleName = QtWidgets.QLineEdit(self.groupBox_42)
        self.tSampleName.setToolTip("")
        self.tSampleName.setStatusTip("")
        self.tSampleName.setWhatsThis("")
        self.tSampleName.setAccessibleName("")
        self.tSampleName.setAccessibleDescription("")
        self.tSampleName.setInputMethodHints(QtCore.Qt.ImhNone)
        self.tSampleName.setText("")
        self.tSampleName.setObjectName("tSampleName")
        self.gridLayout_12.addWidget(self.tSampleName, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox_42, 0, 2, 1, 1)
        self.groupBox_4 = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_4.setFlat(True)
        self.groupBox_4.setCheckable(False)
        self.groupBox_4.setObjectName("groupBox_4")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.groupBox_4)
        self.gridLayout_3.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_3.setSpacing(0)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.tCCDNIRP = QFNumberEdit(self.groupBox_4)
        self.tCCDNIRP.setObjectName("tCCDNIRP")
        self.gridLayout_3.addWidget(self.tCCDNIRP, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox_4, 0, 0, 1, 1)
        self.bCCDBack = QtWidgets.QPushButton(self.tab_3)
        self.bCCDBack.setObjectName("bCCDBack")
        self.gridLayout.addWidget(self.bCCDBack, 4, 0, 1, 1)
        self.groupBox_35 = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_35.setFlat(True)
        self.groupBox_35.setObjectName("groupBox_35")
        self.horizontalLayout_33 = QtWidgets.QHBoxLayout(self.groupBox_35)
        self.horizontalLayout_33.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_33.setObjectName("horizontalLayout_33")
        self.tEMCCDGain = QINumberEdit(self.groupBox_35)
        self.tEMCCDGain.setObjectName("tEMCCDGain")
        self.horizontalLayout_33.addWidget(self.tEMCCDGain)
        self.gridLayout.addWidget(self.groupBox_35, 4, 1, 1, 1)
        self.groupBox_38 = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_38.setFlat(True)
        self.groupBox_38.setCheckable(False)
        self.groupBox_38.setObjectName("groupBox_38")
        self.gridLayout_8 = QtWidgets.QGridLayout(self.groupBox_38)
        self.gridLayout_8.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_8.setSpacing(0)
        self.gridLayout_8.setObjectName("gridLayout_8")
        self.tCCDBGNum = QINumberEdit(self.groupBox_38)
        self.tCCDBGNum.setObjectName("tCCDBGNum")
        self.gridLayout_8.addWidget(self.tCCDBGNum, 0, 0, 1, 1)
        self.bProcessBackgroundSequence = QtWidgets.QToolButton(self.groupBox_38)
        self.bProcessBackgroundSequence.setText("")
        self.bProcessBackgroundSequence.setArrowType(QtCore.Qt.RightArrow)
        self.bProcessBackgroundSequence.setObjectName("bProcessBackgroundSequence")
        self.gridLayout_8.addWidget(self.bProcessBackgroundSequence, 0, 1, 1, 1)
        self.gridLayout.addWidget(self.groupBox_38, 4, 2, 1, 1)
        self.bCCDImage = QtWidgets.QPushButton(self.tab_3)
        self.bCCDImage.setObjectName("bCCDImage")
        self.gridLayout.addWidget(self.bCCDImage, 3, 0, 1, 1)
        self.groupBox_34 = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_34.setFlat(True)
        self.groupBox_34.setObjectName("groupBox_34")
        self.horizontalLayout_32 = QtWidgets.QHBoxLayout(self.groupBox_34)
        self.horizontalLayout_32.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_32.setObjectName("horizontalLayout_32")
        self.tEMCCDExp = QFNumberEdit(self.groupBox_34)
        self.tEMCCDExp.setObjectName("tEMCCDExp")
        self.horizontalLayout_32.addWidget(self.tEMCCDExp)
        self.gridLayout.addWidget(self.groupBox_34, 3, 1, 1, 1)
        self.groupBox_36 = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_36.setFlat(True)
        self.groupBox_36.setCheckable(False)
        self.groupBox_36.setObjectName("groupBox_36")
        self.gridLayout_6 = QtWidgets.QGridLayout(self.groupBox_36)
        self.gridLayout_6.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_6.setSpacing(0)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.tCCDNIRwavelength = QFNumberEdit(self.groupBox_36)
        self.tCCDNIRwavelength.setObjectName("tCCDNIRwavelength")
        self.gridLayout_6.addWidget(self.tCCDNIRwavelength, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox_36, 0, 1, 1, 1)
        self.groupBox_37 = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_37.setFlat(True)
        self.groupBox_37.setCheckable(False)
        self.groupBox_37.setObjectName("groupBox_37")
        self.gridLayout_7 = QtWidgets.QGridLayout(self.groupBox_37)
        self.gridLayout_7.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_7.setSpacing(0)
        self.gridLayout_7.setObjectName("gridLayout_7")
        self.tCCDImageNum = QINumberEdit(self.groupBox_37)
        self.tCCDImageNum.setObjectName("tCCDImageNum")
        self.gridLayout_7.addWidget(self.tCCDImageNum, 0, 0, 1, 1)
        self.bProcessImageSequence = QtWidgets.QToolButton(self.groupBox_37)
        self.bProcessImageSequence.setText("")
        self.bProcessImageSequence.setArrowType(QtCore.Qt.RightArrow)
        self.bProcessImageSequence.setObjectName("bProcessImageSequence")
        self.gridLayout_7.addWidget(self.bProcessImageSequence, 0, 1, 1, 1)
        self.gridLayout.addWidget(self.groupBox_37, 3, 2, 1, 1)
        self.gridLayout.setColumnStretch(0, 1)
        self.verticalLayout_3.addLayout(self.gridLayout)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.groupBox_Series = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_Series.setFlat(True)
        self.groupBox_Series.setObjectName("groupBox_Series")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.groupBox_Series)
        self.horizontalLayout.setContentsMargins(0, 10, 0, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tCCDSeries = QtWidgets.QLineEdit(self.groupBox_Series)
        self.tCCDSeries.setObjectName("tCCDSeries")
        self.horizontalLayout.addWidget(self.tCCDSeries)
        self.horizontalLayout_4.addWidget(self.groupBox_Series)
        self.groupBox_3 = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_3.setFlat(True)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox_3)
        self.verticalLayout_2.setContentsMargins(0, 10, -1, -1)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tSpectrumStep = QtWidgets.QLineEdit(self.groupBox_3)
        self.tSpectrumStep.setObjectName("tSpectrumStep")
        self.verticalLayout_2.addWidget(self.tSpectrumStep)
        self.horizontalLayout_4.addWidget(self.groupBox_3)
        self.verticalLayout_3.addLayout(self.horizontalLayout_4)
        self.groupBox_46 = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_46.setFlat(True)
        self.groupBox_46.setObjectName("groupBox_46")
        self.horizontalLayout_37 = QtWidgets.QHBoxLayout(self.groupBox_46)
        self.horizontalLayout_37.setObjectName("horizontalLayout_37")
        self.tCCDComments = QtWidgets.QTextEdit(self.groupBox_46)
        self.tCCDComments.setObjectName("tCCDComments")
        self.horizontalLayout_37.addWidget(self.tCCDComments)
        self.verticalLayout_3.addWidget(self.groupBox_46)
        self.tabWidget_3.addTab(self.tab_3, "")
        self.tab_4 = QtWidgets.QWidget()
        self.tab_4.setObjectName("tab_4")
        self.horizontalLayout_52 = QtWidgets.QHBoxLayout(self.tab_4)
        self.horizontalLayout_52.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_52.setObjectName("horizontalLayout_52")
        self.gridLayout_17 = QtWidgets.QGridLayout()
        self.gridLayout_17.setObjectName("gridLayout_17")
        self.groupBox = QtWidgets.QGroupBox(self.tab_4)
        self.groupBox.setFlat(True)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.groupBox)
        self.horizontalLayout_2.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.tCCDNIRAlpha = QtWidgets.QLineEdit(self.groupBox)
        self.tCCDNIRAlpha.setObjectName("tCCDNIRAlpha")
        self.horizontalLayout_2.addWidget(self.tCCDNIRAlpha)
        self.gridLayout_17.addWidget(self.groupBox, 0, 0, 1, 1)
        self.groupBox_2 = QtWidgets.QGroupBox(self.tab_4)
        self.groupBox_2.setFlat(True)
        self.groupBox_2.setObjectName("groupBox_2")
        self.horizontalLayout_44 = QtWidgets.QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_44.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_44.setObjectName("horizontalLayout_44")
        self.tCCDSampleTemp = QtWidgets.QLineEdit(self.groupBox_2)
        self.tCCDSampleTemp.setObjectName("tCCDSampleTemp")
        self.horizontalLayout_44.addWidget(self.tCCDSampleTemp)
        self.gridLayout_17.addWidget(self.groupBox_2, 1, 0, 1, 1)
        self.groupBox_44 = QtWidgets.QGroupBox(self.tab_4)
        self.groupBox_44.setFlat(True)
        self.groupBox_44.setCheckable(False)
        self.groupBox_44.setObjectName("groupBox_44")
        self.gridLayout_14 = QtWidgets.QGridLayout(self.groupBox_44)
        self.gridLayout_14.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_14.setSpacing(0)
        self.gridLayout_14.setObjectName("gridLayout_14")
        self.tCCDYMax = QtWidgets.QLineEdit(self.groupBox_44)
        self.tCCDYMax.setObjectName("tCCDYMax")
        self.gridLayout_14.addWidget(self.tCCDYMax, 0, 0, 1, 1)
        self.gridLayout_17.addWidget(self.groupBox_44, 1, 2, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_17.addItem(spacerItem, 3, 0, 1, 1)
        self.groupBox_45 = QtWidgets.QGroupBox(self.tab_4)
        self.groupBox_45.setFlat(True)
        self.groupBox_45.setCheckable(False)
        self.groupBox_45.setObjectName("groupBox_45")
        self.gridLayout_15 = QtWidgets.QGridLayout(self.groupBox_45)
        self.gridLayout_15.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_15.setSpacing(0)
        self.gridLayout_15.setObjectName("gridLayout_15")
        self.tCCDSlits = QtWidgets.QLineEdit(self.groupBox_45)
        self.tCCDSlits.setObjectName("tCCDSlits")
        self.gridLayout_15.addWidget(self.tCCDSlits, 0, 0, 1, 1)
        self.gridLayout_17.addWidget(self.groupBox_45, 0, 2, 1, 1)
        self.groupBox_43 = QtWidgets.QGroupBox(self.tab_4)
        self.groupBox_43.setFlat(True)
        self.groupBox_43.setCheckable(False)
        self.groupBox_43.setObjectName("groupBox_43")
        self.gridLayout_13 = QtWidgets.QGridLayout(self.groupBox_43)
        self.gridLayout_13.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_13.setSpacing(0)
        self.gridLayout_13.setObjectName("gridLayout_13")
        self.tCCDYMin = QtWidgets.QLineEdit(self.groupBox_43)
        self.tCCDYMin.setObjectName("tCCDYMin")
        self.gridLayout_13.addWidget(self.tCCDYMin, 0, 0, 1, 1)
        self.gridLayout_17.addWidget(self.groupBox_43, 1, 1, 1, 1)
        self.groupBox_5 = QtWidgets.QGroupBox(self.tab_4)
        self.groupBox_5.setFlat(True)
        self.groupBox_5.setObjectName("groupBox_5")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.groupBox_5)
        self.horizontalLayout_3.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.tCCDNIRGamma = QtWidgets.QLineEdit(self.groupBox_5)
        self.tCCDNIRGamma.setObjectName("tCCDNIRGamma")
        self.horizontalLayout_3.addWidget(self.tCCDNIRGamma)
        self.gridLayout_17.addWidget(self.groupBox_5, 0, 1, 1, 1)
        self.horizontalLayout_52.addLayout(self.gridLayout_17)
        self.tabWidget_3.addTab(self.tab_4, "")
        self.splitterImages = QtWidgets.QSplitter(self.splitterTop)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(10)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.splitterImages.sizePolicy().hasHeightForWidth())
        self.splitterImages.setSizePolicy(sizePolicy)
        self.splitterImages.setOrientation(QtCore.Qt.Vertical)
        self.splitterImages.setObjectName("splitterImages")
        self.gCCDImage = ImageViewWithPlotItemContainer(self.splitterImages)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.gCCDImage.sizePolicy().hasHeightForWidth())
        self.gCCDImage.setSizePolicy(sizePolicy)
        self.gCCDImage.setObjectName("gCCDImage")
        self.gCCDBack = ImageViewWithPlotItemContainer(self.splitterImages)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.gCCDBack.sizePolicy().hasHeightForWidth())
        self.gCCDBack.setSizePolicy(sizePolicy)
        self.gCCDBack.setObjectName("gCCDBack")
        self.gCCDBin = PlotWidget(self.splitterAll)
        self.gCCDBin.setObjectName("gCCDBin")
        self.layoutWidget = QtWidgets.QWidget(self.splitterAll)
        self.layoutWidget.setObjectName("layoutWidget")
        self.horizontalLayout_34 = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout_34.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_34.setObjectName("horizontalLayout_34")
        self.pCCD = QtWidgets.QProgressBar(self.layoutWidget)
        self.pCCD.setProperty("value", 0)
        self.pCCD.setObjectName("pCCD")
        self.horizontalLayout_34.addWidget(self.pCCD)
        self.lCCDProg = QtWidgets.QLabel(self.layoutWidget)
        self.lCCDProg.setObjectName("lCCDProg")
        self.horizontalLayout_34.addWidget(self.lCCDProg)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_34.addItem(spacerItem1)
        self.horizontalLayout_34.setStretch(0, 9)
        self.horizontalLayout_34.setStretch(1, 1)
        self.horizontalLayout_34.setStretch(2, 1)
        self.verticalLayout.addWidget(self.splitterAll)

        self.retranslateUi(PL)
        self.tabWidget_3.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(PL)
        PL.setTabOrder(self.tCCDNIRP, self.tCCDNIRwavelength)
        PL.setTabOrder(self.tCCDNIRwavelength, self.tSampleName)
        PL.setTabOrder(self.tSampleName, self.bCCDImage)
        PL.setTabOrder(self.bCCDImage, self.tEMCCDExp)
        PL.setTabOrder(self.tEMCCDExp, self.tCCDImageNum)
        PL.setTabOrder(self.tCCDImageNum, self.bCCDBack)
        PL.setTabOrder(self.bCCDBack, self.tEMCCDGain)
        PL.setTabOrder(self.tEMCCDGain, self.tCCDBGNum)
        PL.setTabOrder(self.tCCDBGNum, self.tCCDSeries)
        PL.setTabOrder(self.tCCDSeries, self.tSpectrumStep)
        PL.setTabOrder(self.tSpectrumStep, self.tCCDComments)
        PL.setTabOrder(self.tCCDComments, self.tCCDNIRAlpha)
        PL.setTabOrder(self.tCCDNIRAlpha, self.tCCDNIRGamma)
        PL.setTabOrder(self.tCCDNIRGamma, self.tCCDSlits)
        PL.setTabOrder(self.tCCDSlits, self.tCCDSampleTemp)
        PL.setTabOrder(self.tCCDSampleTemp, self.tCCDYMin)
        PL.setTabOrder(self.tCCDYMin, self.tCCDYMax)
        PL.setTabOrder(self.tCCDYMax, self.bProcessBackgroundSequence)
        PL.setTabOrder(self.bProcessBackgroundSequence, self.gCCDBack)
        PL.setTabOrder(self.gCCDBack, self.gCCDBin)
        PL.setTabOrder(self.gCCDBin, self.tabWidget_3)
        PL.setTabOrder(self.tabWidget_3, self.gCCDImage)
        PL.setTabOrder(self.gCCDImage, self.bProcessImageSequence)

    def retranslateUi(self, PL):
        _translate = QtCore.QCoreApplication.translate
        PL.setWindowTitle(_translate("PL", "Form"))
        self.groupBox_42.setTitle(_translate("PL", "Sample"))
        self.groupBox_4.setTitle(_translate("PL", "NIR Power (mW)"))
        self.tCCDNIRP.setText(_translate("PL", "0"))
        self.bCCDBack.setText(_translate("PL", "Take Background"))
        self.groupBox_35.setTitle(_translate("PL", "Gain"))
        self.tEMCCDGain.setText(_translate("PL", "1"))
        self.groupBox_38.setTitle(_translate("PL", "Bg Number"))
        self.tCCDBGNum.setText(_translate("PL", "0"))
        self.bCCDImage.setText(_translate("PL", "Take Image"))
        self.groupBox_34.setTitle(_translate("PL", "Exp (s)"))
        self.tEMCCDExp.setText(_translate("PL", "0.5"))
        self.groupBox_36.setTitle(_translate("PL", "NIR Wl (nm)"))
        self.tCCDNIRwavelength.setText(_translate("PL", "0"))
        self.groupBox_37.setTitle(_translate("PL", "Image Number"))
        self.tCCDImageNum.setText(_translate("PL", "0"))
        self.groupBox_Series.setTitle(_translate("PL", "Series"))
        self.tCCDSeries.setToolTip(_translate("PL", "NIRP, NIRW, FELF, FELP, SLITS, SPECL"))
        self.groupBox_3.setTitle(_translate("PL", "Spectrum step"))
        self.groupBox_46.setTitle(_translate("PL", "Comments"))
        self.tabWidget_3.setTabText(self.tabWidget_3.indexOf(self.tab_3), _translate("PL", "Main Settings"))
        self.groupBox.setTitle(_translate("PL", "NIR α"))
        self.groupBox_2.setTitle(_translate("PL", "Sample Temp"))
        self.groupBox_44.setTitle(_translate("PL", "Ymax"))
        self.tCCDYMax.setText(_translate("PL", "400"))
        self.groupBox_45.setTitle(_translate("PL", "Slits"))
        self.tCCDSlits.setText(_translate("PL", "0"))
        self.groupBox_43.setTitle(_translate("PL", "Ymin"))
        self.tCCDYMin.setText(_translate("PL", "0"))
        self.groupBox_5.setTitle(_translate("PL", "NIR γ"))
        self.tabWidget_3.setTabText(self.tabWidget_3.indexOf(self.tab_4), _translate("PL", "Other Settings"))
        self.lCCDProg.setText(_translate("PL", "Done."))

from .ImageViewWithPlotItemContainer import ImageViewWithPlotItemContainer
from InstsAndQt.customQt import QFNumberEdit, QINumberEdit
from pyqtgraph import PlotWidget
