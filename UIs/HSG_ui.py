# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'HSG.ui'
#
# Created: Fri Nov  6 20:17:08 2015
#      by: PyQt4 UI code generator 4.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_HSG(object):
    def setupUi(self, HSG):
        HSG.setObjectName(_fromUtf8("HSG"))
        HSG.resize(838, 690)
        self.horizontalLayout = QtGui.QHBoxLayout(HSG)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.splitterAll = QtGui.QSplitter(HSG)
        self.splitterAll.setOrientation(QtCore.Qt.Vertical)
        self.splitterAll.setObjectName(_fromUtf8("splitterAll"))
        self.splitterTop = QtGui.QSplitter(self.splitterAll)
        self.splitterTop.setOrientation(QtCore.Qt.Horizontal)
        self.splitterTop.setObjectName(_fromUtf8("splitterTop"))
        self.tabWidget_3 = QtGui.QTabWidget(self.splitterTop)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget_3.sizePolicy().hasHeightForWidth())
        self.tabWidget_3.setSizePolicy(sizePolicy)
        self.tabWidget_3.setObjectName(_fromUtf8("tabWidget_3"))
        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName(_fromUtf8("tab_3"))
        self.verticalLayout = QtGui.QVBoxLayout(self.tab_3)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.verticalLayout_9 = QtGui.QVBoxLayout()
        self.verticalLayout_9.setObjectName(_fromUtf8("verticalLayout_9"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.groupBox_42 = QtGui.QGroupBox(self.tab_3)
        self.groupBox_42.setFlat(True)
        self.groupBox_42.setCheckable(False)
        self.groupBox_42.setObjectName(_fromUtf8("groupBox_42"))
        self.gridLayout_12 = QtGui.QGridLayout(self.groupBox_42)
        self.gridLayout_12.setSpacing(0)
        self.gridLayout_12.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_12.setObjectName(_fromUtf8("gridLayout_12"))
        self.tSampleName = QtGui.QLineEdit(self.groupBox_42)
        self.tSampleName.setToolTip(_fromUtf8(""))
        self.tSampleName.setStatusTip(_fromUtf8(""))
        self.tSampleName.setWhatsThis(_fromUtf8(""))
        self.tSampleName.setAccessibleName(_fromUtf8(""))
        self.tSampleName.setAccessibleDescription(_fromUtf8(""))
        self.tSampleName.setInputMethodHints(QtCore.Qt.ImhNone)
        self.tSampleName.setText(_fromUtf8(""))
        self.tSampleName.setObjectName(_fromUtf8("tSampleName"))
        self.gridLayout_12.addWidget(self.tSampleName, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox_42, 0, 2, 1, 1)
        self.groupBox_4 = QtGui.QGroupBox(self.tab_3)
        self.groupBox_4.setFlat(True)
        self.groupBox_4.setCheckable(False)
        self.groupBox_4.setObjectName(_fromUtf8("groupBox_4"))
        self.gridLayout_3 = QtGui.QGridLayout(self.groupBox_4)
        self.gridLayout_3.setSpacing(0)
        self.gridLayout_3.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.tCCDNIRP = QFNumberEdit(self.groupBox_4)
        self.tCCDNIRP.setObjectName(_fromUtf8("tCCDNIRP"))
        self.gridLayout_3.addWidget(self.tCCDNIRP, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox_4, 0, 0, 1, 1)
        self.bCCDBack = QtGui.QPushButton(self.tab_3)
        self.bCCDBack.setObjectName(_fromUtf8("bCCDBack"))
        self.gridLayout.addWidget(self.bCCDBack, 5, 0, 1, 1)
        self.groupBox_35 = QtGui.QGroupBox(self.tab_3)
        self.groupBox_35.setFlat(True)
        self.groupBox_35.setObjectName(_fromUtf8("groupBox_35"))
        self.horizontalLayout_33 = QtGui.QHBoxLayout(self.groupBox_35)
        self.horizontalLayout_33.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_33.setObjectName(_fromUtf8("horizontalLayout_33"))
        self.tEMCCDGain = QINumberEdit(self.groupBox_35)
        self.tEMCCDGain.setObjectName(_fromUtf8("tEMCCDGain"))
        self.horizontalLayout_33.addWidget(self.tEMCCDGain)
        self.gridLayout.addWidget(self.groupBox_35, 5, 1, 1, 1)
        self.groupBox_38 = QtGui.QGroupBox(self.tab_3)
        self.groupBox_38.setFlat(True)
        self.groupBox_38.setCheckable(False)
        self.groupBox_38.setObjectName(_fromUtf8("groupBox_38"))
        self.gridLayout_8 = QtGui.QGridLayout(self.groupBox_38)
        self.gridLayout_8.setSpacing(0)
        self.gridLayout_8.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_8.setObjectName(_fromUtf8("gridLayout_8"))
        self.tCCDBGNum = QINumberEdit(self.groupBox_38)
        self.tCCDBGNum.setObjectName(_fromUtf8("tCCDBGNum"))
        self.gridLayout_8.addWidget(self.tCCDBGNum, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox_38, 5, 2, 1, 1)
        self.bCCDImage = QtGui.QPushButton(self.tab_3)
        self.bCCDImage.setObjectName(_fromUtf8("bCCDImage"))
        self.gridLayout.addWidget(self.bCCDImage, 4, 0, 1, 1)
        self.groupBox_34 = QtGui.QGroupBox(self.tab_3)
        self.groupBox_34.setFlat(True)
        self.groupBox_34.setObjectName(_fromUtf8("groupBox_34"))
        self.horizontalLayout_32 = QtGui.QHBoxLayout(self.groupBox_34)
        self.horizontalLayout_32.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_32.setObjectName(_fromUtf8("horizontalLayout_32"))
        self.tEMCCDExp = QFNumberEdit(self.groupBox_34)
        self.tEMCCDExp.setObjectName(_fromUtf8("tEMCCDExp"))
        self.horizontalLayout_32.addWidget(self.tEMCCDExp)
        self.gridLayout.addWidget(self.groupBox_34, 4, 1, 1, 1)
        self.groupBox_36 = QtGui.QGroupBox(self.tab_3)
        self.groupBox_36.setFlat(True)
        self.groupBox_36.setCheckable(False)
        self.groupBox_36.setObjectName(_fromUtf8("groupBox_36"))
        self.gridLayout_6 = QtGui.QGridLayout(self.groupBox_36)
        self.gridLayout_6.setSpacing(0)
        self.gridLayout_6.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_6.setObjectName(_fromUtf8("gridLayout_6"))
        self.tCCDNIRwavelength = QFNumberEdit(self.groupBox_36)
        self.tCCDNIRwavelength.setObjectName(_fromUtf8("tCCDNIRwavelength"))
        self.gridLayout_6.addWidget(self.tCCDNIRwavelength, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox_36, 0, 1, 1, 1)
        self.groupBox_37 = QtGui.QGroupBox(self.tab_3)
        self.groupBox_37.setFlat(True)
        self.groupBox_37.setCheckable(False)
        self.groupBox_37.setObjectName(_fromUtf8("groupBox_37"))
        self.gridLayout_7 = QtGui.QGridLayout(self.groupBox_37)
        self.gridLayout_7.setSpacing(0)
        self.gridLayout_7.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_7.setObjectName(_fromUtf8("gridLayout_7"))
        self.tCCDImageNum = QINumberEdit(self.groupBox_37)
        self.tCCDImageNum.setObjectName(_fromUtf8("tCCDImageNum"))
        self.gridLayout_7.addWidget(self.tCCDImageNum, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox_37, 4, 2, 1, 1)
        self.groupBox_40 = QtGui.QGroupBox(self.tab_3)
        self.groupBox_40.setFlat(True)
        self.groupBox_40.setCheckable(False)
        self.groupBox_40.setObjectName(_fromUtf8("groupBox_40"))
        self.gridLayout_10 = QtGui.QGridLayout(self.groupBox_40)
        self.gridLayout_10.setSpacing(0)
        self.gridLayout_10.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_10.setObjectName(_fromUtf8("gridLayout_10"))
        self.tCCDFELP = QFNumberEdit(self.groupBox_40)
        self.tCCDFELP.setObjectName(_fromUtf8("tCCDFELP"))
        self.gridLayout_10.addWidget(self.tCCDFELP, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBox_40, 2, 0, 1, 1)
        self.groupBox_59 = QtGui.QGroupBox(self.tab_3)
        self.groupBox_59.setEnabled(False)
        self.groupBox_59.setFlat(True)
        self.groupBox_59.setObjectName(_fromUtf8("groupBox_59"))
        self.horizontalLayout_56 = QtGui.QHBoxLayout(self.groupBox_59)
        self.horizontalLayout_56.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_56.setObjectName(_fromUtf8("horizontalLayout_56"))
        self.tCCDEField = QtGui.QLineEdit(self.groupBox_59)
        self.tCCDEField.setObjectName(_fromUtf8("tCCDEField"))
        self.horizontalLayout_56.addWidget(self.tCCDEField)
        self.gridLayout.addWidget(self.groupBox_59, 2, 1, 1, 1)
        self.groupBox_60 = QtGui.QGroupBox(self.tab_3)
        self.groupBox_60.setEnabled(False)
        self.groupBox_60.setFlat(True)
        self.groupBox_60.setObjectName(_fromUtf8("groupBox_60"))
        self.horizontalLayout_57 = QtGui.QHBoxLayout(self.groupBox_60)
        self.horizontalLayout_57.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_57.setObjectName(_fromUtf8("horizontalLayout_57"))
        self.tCCDIntensity = QtGui.QLineEdit(self.groupBox_60)
        self.tCCDIntensity.setObjectName(_fromUtf8("tCCDIntensity"))
        self.horizontalLayout_57.addWidget(self.tCCDIntensity)
        self.gridLayout.addWidget(self.groupBox_60, 2, 2, 1, 1)
        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 1)
        self.gridLayout.setColumnStretch(2, 1)
        self.verticalLayout_9.addLayout(self.gridLayout)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.groupBox_Series = QtGui.QGroupBox(self.tab_3)
        self.groupBox_Series.setFlat(True)
        self.groupBox_Series.setObjectName(_fromUtf8("groupBox_Series"))
        self.horizontalLayout_5 = QtGui.QHBoxLayout(self.groupBox_Series)
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.tCCDSeries = QtGui.QLineEdit(self.groupBox_Series)
        self.tCCDSeries.setObjectName(_fromUtf8("tCCDSeries"))
        self.horizontalLayout_5.addWidget(self.tCCDSeries)
        self.horizontalLayout_3.addWidget(self.groupBox_Series)
        self.groupBox = QtGui.QGroupBox(self.tab_3)
        self.groupBox.setFlat(True)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.horizontalLayout_6 = QtGui.QHBoxLayout(self.groupBox)
        self.horizontalLayout_6.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_6.setObjectName(_fromUtf8("horizontalLayout_6"))
        self.tSpectrumStep = QtGui.QLineEdit(self.groupBox)
        self.tSpectrumStep.setObjectName(_fromUtf8("tSpectrumStep"))
        self.horizontalLayout_6.addWidget(self.tSpectrumStep)
        self.horizontalLayout_3.addWidget(self.groupBox)
        self.verticalLayout_9.addLayout(self.horizontalLayout_3)
        self.groupBox_46 = QtGui.QGroupBox(self.tab_3)
        self.groupBox_46.setFlat(True)
        self.groupBox_46.setObjectName(_fromUtf8("groupBox_46"))
        self.horizontalLayout_37 = QtGui.QHBoxLayout(self.groupBox_46)
        self.horizontalLayout_37.setObjectName(_fromUtf8("horizontalLayout_37"))
        self.tCCDComments = QtGui.QTextEdit(self.groupBox_46)
        self.tCCDComments.setObjectName(_fromUtf8("tCCDComments"))
        self.horizontalLayout_37.addWidget(self.tCCDComments)
        self.verticalLayout_9.addWidget(self.groupBox_46)
        self.verticalLayout_9.setStretch(2, 1)
        self.verticalLayout.addLayout(self.verticalLayout_9)
        self.tabWidget_3.addTab(self.tab_3, _fromUtf8(""))
        self.tab_4 = QtGui.QWidget()
        self.tab_4.setObjectName(_fromUtf8("tab_4"))
        self.horizontalLayout_52 = QtGui.QHBoxLayout(self.tab_4)
        self.horizontalLayout_52.setObjectName(_fromUtf8("horizontalLayout_52"))
        self.gridLayout_17 = QtGui.QGridLayout()
        self.gridLayout_17.setObjectName(_fromUtf8("gridLayout_17"))
        self.groupBox_55 = QtGui.QGroupBox(self.tab_4)
        self.groupBox_55.setFlat(True)
        self.groupBox_55.setObjectName(_fromUtf8("groupBox_55"))
        self.horizontalLayout_53 = QtGui.QHBoxLayout(self.groupBox_55)
        self.horizontalLayout_53.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_53.setObjectName(_fromUtf8("horizontalLayout_53"))
        self.tCCDSpotSize = QFNumberEdit(self.groupBox_55)
        self.tCCDSpotSize.setObjectName(_fromUtf8("tCCDSpotSize"))
        self.horizontalLayout_53.addWidget(self.tCCDSpotSize)
        self.gridLayout_17.addWidget(self.groupBox_55, 2, 0, 1, 1)
        self.groupBox_45 = QtGui.QGroupBox(self.tab_4)
        self.groupBox_45.setFlat(True)
        self.groupBox_45.setCheckable(False)
        self.groupBox_45.setObjectName(_fromUtf8("groupBox_45"))
        self.gridLayout_15 = QtGui.QGridLayout(self.groupBox_45)
        self.gridLayout_15.setSpacing(0)
        self.gridLayout_15.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_15.setObjectName(_fromUtf8("gridLayout_15"))
        self.tCCDSlits = QtGui.QLineEdit(self.groupBox_45)
        self.tCCDSlits.setObjectName(_fromUtf8("tCCDSlits"))
        self.gridLayout_15.addWidget(self.tCCDSlits, 0, 0, 1, 1)
        self.gridLayout_17.addWidget(self.groupBox_45, 0, 3, 1, 1)
        self.groupBox_39 = QtGui.QGroupBox(self.tab_4)
        self.groupBox_39.setFlat(True)
        self.groupBox_39.setCheckable(False)
        self.groupBox_39.setObjectName(_fromUtf8("groupBox_39"))
        self.gridLayout_9 = QtGui.QGridLayout(self.groupBox_39)
        self.gridLayout_9.setSpacing(0)
        self.gridLayout_9.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_9.setObjectName(_fromUtf8("gridLayout_9"))
        self.tCCDFELFreq = QFNumberEdit(self.groupBox_39)
        self.tCCDFELFreq.setObjectName(_fromUtf8("tCCDFELFreq"))
        self.gridLayout_9.addWidget(self.tCCDFELFreq, 0, 0, 1, 1)
        self.gridLayout_17.addWidget(self.groupBox_39, 0, 0, 1, 1)
        self.groupBox_58 = QtGui.QGroupBox(self.tab_4)
        self.groupBox_58.setFlat(True)
        self.groupBox_58.setObjectName(_fromUtf8("groupBox_58"))
        self.horizontalLayout_55 = QtGui.QHBoxLayout(self.groupBox_58)
        self.horizontalLayout_55.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_55.setObjectName(_fromUtf8("horizontalLayout_55"))
        self.tCCDEffectiveField = QFNumberEdit(self.groupBox_58)
        self.tCCDEffectiveField.setObjectName(_fromUtf8("tCCDEffectiveField"))
        self.horizontalLayout_55.addWidget(self.tCCDEffectiveField)
        self.gridLayout_17.addWidget(self.groupBox_58, 2, 3, 1, 1)
        self.groupBox_2 = QtGui.QGroupBox(self.tab_4)
        self.groupBox_2.setFlat(True)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.horizontalLayout_44 = QtGui.QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_44.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_44.setObjectName(_fromUtf8("horizontalLayout_44"))
        self.tCCDSampleTemp = QtGui.QLineEdit(self.groupBox_2)
        self.tCCDSampleTemp.setObjectName(_fromUtf8("tCCDSampleTemp"))
        self.horizontalLayout_44.addWidget(self.tCCDSampleTemp)
        self.gridLayout_17.addWidget(self.groupBox_2, 1, 0, 1, 1)
        self.groupBox_57 = QtGui.QGroupBox(self.tab_4)
        self.groupBox_57.setFlat(True)
        self.groupBox_57.setObjectName(_fromUtf8("groupBox_57"))
        self.horizontalLayout_51 = QtGui.QHBoxLayout(self.groupBox_57)
        self.horizontalLayout_51.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_51.setObjectName(_fromUtf8("horizontalLayout_51"))
        self.tCCDWindowTransmission = QFNumberEdit(self.groupBox_57)
        self.tCCDWindowTransmission.setObjectName(_fromUtf8("tCCDWindowTransmission"))
        self.horizontalLayout_51.addWidget(self.tCCDWindowTransmission)
        self.gridLayout_17.addWidget(self.groupBox_57, 2, 2, 1, 1)
        self.groupBox_44 = QtGui.QGroupBox(self.tab_4)
        self.groupBox_44.setFlat(True)
        self.groupBox_44.setCheckable(False)
        self.groupBox_44.setObjectName(_fromUtf8("groupBox_44"))
        self.gridLayout_14 = QtGui.QGridLayout(self.groupBox_44)
        self.gridLayout_14.setSpacing(0)
        self.gridLayout_14.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_14.setObjectName(_fromUtf8("gridLayout_14"))
        self.tCCDYMax = QtGui.QLineEdit(self.groupBox_44)
        self.tCCDYMax.setObjectName(_fromUtf8("tCCDYMax"))
        self.gridLayout_14.addWidget(self.tCCDYMax, 0, 0, 1, 1)
        self.gridLayout_17.addWidget(self.groupBox_44, 1, 3, 1, 1)
        self.groupBox_43 = QtGui.QGroupBox(self.tab_4)
        self.groupBox_43.setFlat(True)
        self.groupBox_43.setCheckable(False)
        self.groupBox_43.setObjectName(_fromUtf8("groupBox_43"))
        self.gridLayout_13 = QtGui.QGridLayout(self.groupBox_43)
        self.gridLayout_13.setSpacing(0)
        self.gridLayout_13.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_13.setObjectName(_fromUtf8("gridLayout_13"))
        self.tCCDYMin = QtGui.QLineEdit(self.groupBox_43)
        self.tCCDYMin.setObjectName(_fromUtf8("tCCDYMin"))
        self.gridLayout_13.addWidget(self.tCCDYMin, 0, 0, 1, 1)
        self.gridLayout_17.addWidget(self.groupBox_43, 1, 2, 1, 1)
        self.groupBox_41 = QtGui.QGroupBox(self.tab_4)
        self.groupBox_41.setFlat(True)
        self.groupBox_41.setCheckable(False)
        self.groupBox_41.setObjectName(_fromUtf8("groupBox_41"))
        self.gridLayout_11 = QtGui.QGridLayout(self.groupBox_41)
        self.gridLayout_11.setSpacing(0)
        self.gridLayout_11.setContentsMargins(0, 10, 0, 0)
        self.gridLayout_11.setObjectName(_fromUtf8("gridLayout_11"))
        self.tCCDFELRR = QtGui.QLineEdit(self.groupBox_41)
        self.tCCDFELRR.setObjectName(_fromUtf8("tCCDFELRR"))
        self.gridLayout_11.addWidget(self.tCCDFELRR, 0, 0, 1, 1)
        self.gridLayout_17.addWidget(self.groupBox_41, 0, 2, 1, 1)
        self.groupBox_3 = QtGui.QGroupBox(self.tab_4)
        self.groupBox_3.setFlat(True)
        self.groupBox_3.setObjectName(_fromUtf8("groupBox_3"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.groupBox_3)
        self.horizontalLayout_2.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.tCCDFELPol = QtGui.QLineEdit(self.groupBox_3)
        self.tCCDFELPol.setObjectName(_fromUtf8("tCCDFELPol"))
        self.horizontalLayout_2.addWidget(self.tCCDFELPol)
        self.gridLayout_17.addWidget(self.groupBox_3, 3, 2, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_17.addItem(spacerItem, 4, 3, 1, 1)
        self.groupBox_5 = QtGui.QGroupBox(self.tab_4)
        self.groupBox_5.setFlat(True)
        self.groupBox_5.setObjectName(_fromUtf8("groupBox_5"))
        self.horizontalLayout_4 = QtGui.QHBoxLayout(self.groupBox_5)
        self.horizontalLayout_4.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.tCCDNIRPol = QtGui.QLineEdit(self.groupBox_5)
        self.tCCDNIRPol.setObjectName(_fromUtf8("tCCDNIRPol"))
        self.horizontalLayout_4.addWidget(self.tCCDNIRPol)
        self.gridLayout_17.addWidget(self.groupBox_5, 3, 0, 1, 1)
        self.horizontalLayout_52.addLayout(self.gridLayout_17)
        self.tabWidget_3.addTab(self.tab_4, _fromUtf8(""))
        self.splitterImages = QtGui.QSplitter(self.splitterTop)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(10)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.splitterImages.sizePolicy().hasHeightForWidth())
        self.splitterImages.setSizePolicy(sizePolicy)
        self.splitterImages.setOrientation(QtCore.Qt.Vertical)
        self.splitterImages.setObjectName(_fromUtf8("splitterImages"))
        self.gCCDImage = ImageViewWithPlotItemContainer(self.splitterImages)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.gCCDImage.sizePolicy().hasHeightForWidth())
        self.gCCDImage.setSizePolicy(sizePolicy)
        self.gCCDImage.setObjectName(_fromUtf8("gCCDImage"))
        self.gCCDBack = ImageViewWithPlotItemContainer(self.splitterImages)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.gCCDBack.sizePolicy().hasHeightForWidth())
        self.gCCDBack.setSizePolicy(sizePolicy)
        self.gCCDBack.setObjectName(_fromUtf8("gCCDBack"))
        self.gCCDBin = PlotWidget(self.splitterAll)
        self.gCCDBin.setObjectName(_fromUtf8("gCCDBin"))
        self.layoutWidget = QtGui.QWidget(self.splitterAll)
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.horizontalLayout_34 = QtGui.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout_34.setContentsMargins(-1, -1, -1, 0)
        self.horizontalLayout_34.setObjectName(_fromUtf8("horizontalLayout_34"))
        self.pCCD = QtGui.QProgressBar(self.layoutWidget)
        self.pCCD.setProperty("value", 0)
        self.pCCD.setObjectName(_fromUtf8("pCCD"))
        self.horizontalLayout_34.addWidget(self.pCCD)
        self.lCCDProg = QtGui.QLabel(self.layoutWidget)
        self.lCCDProg.setObjectName(_fromUtf8("lCCDProg"))
        self.horizontalLayout_34.addWidget(self.lCCDProg)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_34.addItem(spacerItem1)
        self.groupBox_56 = QtGui.QGroupBox(self.layoutWidget)
        self.groupBox_56.setFlat(True)
        self.groupBox_56.setObjectName(_fromUtf8("groupBox_56"))
        self.horizontalLayout_54 = QtGui.QHBoxLayout(self.groupBox_56)
        self.horizontalLayout_54.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_54.setObjectName(_fromUtf8("horizontalLayout_54"))
        self.tCCDSidebandNumber = QFNumberEdit(self.groupBox_56)
        self.tCCDSidebandNumber.setObjectName(_fromUtf8("tCCDSidebandNumber"))
        self.horizontalLayout_54.addWidget(self.tCCDSidebandNumber)
        self.horizontalLayout_34.addWidget(self.groupBox_56)
        self.groupBox_54 = QtGui.QGroupBox(self.layoutWidget)
        self.groupBox_54.setFlat(True)
        self.groupBox_54.setObjectName(_fromUtf8("groupBox_54"))
        self.horizontalLayout_50 = QtGui.QHBoxLayout(self.groupBox_54)
        self.horizontalLayout_50.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_50.setObjectName(_fromUtf8("horizontalLayout_50"))
        self.tCCDFELPulses = QtGui.QLineEdit(self.groupBox_54)
        self.tCCDFELPulses.setReadOnly(True)
        self.tCCDFELPulses.setObjectName(_fromUtf8("tCCDFELPulses"))
        self.horizontalLayout_50.addWidget(self.tCCDFELPulses)
        self.horizontalLayout_34.addWidget(self.groupBox_54)
        self.horizontalLayout_34.setStretch(0, 9)
        self.horizontalLayout_34.setStretch(1, 1)
        self.horizontalLayout_34.setStretch(2, 1)
        self.horizontalLayout_34.setStretch(4, 1)
        self.horizontalLayout.addWidget(self.splitterAll)

        self.retranslateUi(HSG)
        self.tabWidget_3.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(HSG)
        HSG.setTabOrder(self.tCCDNIRP, self.tCCDNIRwavelength)
        HSG.setTabOrder(self.tCCDNIRwavelength, self.tSampleName)
        HSG.setTabOrder(self.tSampleName, self.tCCDFELP)
        HSG.setTabOrder(self.tCCDFELP, self.tCCDEField)
        HSG.setTabOrder(self.tCCDEField, self.tCCDIntensity)
        HSG.setTabOrder(self.tCCDIntensity, self.bCCDImage)
        HSG.setTabOrder(self.bCCDImage, self.tEMCCDExp)
        HSG.setTabOrder(self.tEMCCDExp, self.tCCDImageNum)
        HSG.setTabOrder(self.tCCDImageNum, self.bCCDBack)
        HSG.setTabOrder(self.bCCDBack, self.tEMCCDGain)
        HSG.setTabOrder(self.tEMCCDGain, self.tCCDBGNum)
        HSG.setTabOrder(self.tCCDBGNum, self.tCCDComments)
        HSG.setTabOrder(self.tCCDComments, self.tCCDFELFreq)
        HSG.setTabOrder(self.tCCDFELFreq, self.tCCDFELRR)
        HSG.setTabOrder(self.tCCDFELRR, self.tCCDSlits)
        HSG.setTabOrder(self.tCCDSlits, self.tCCDSampleTemp)
        HSG.setTabOrder(self.tCCDSampleTemp, self.tCCDYMin)
        HSG.setTabOrder(self.tCCDYMin, self.tCCDYMax)
        HSG.setTabOrder(self.tCCDYMax, self.tCCDSpotSize)
        HSG.setTabOrder(self.tCCDSpotSize, self.tCCDWindowTransmission)
        HSG.setTabOrder(self.tCCDWindowTransmission, self.tCCDEffectiveField)
        HSG.setTabOrder(self.tCCDEffectiveField, self.tabWidget_3)
        HSG.setTabOrder(self.tabWidget_3, self.gCCDBack)
        HSG.setTabOrder(self.gCCDBack, self.tCCDSidebandNumber)
        HSG.setTabOrder(self.tCCDSidebandNumber, self.gCCDImage)
        HSG.setTabOrder(self.gCCDImage, self.tCCDFELPulses)
        HSG.setTabOrder(self.tCCDFELPulses, self.gCCDBin)

    def retranslateUi(self, HSG):
        HSG.setWindowTitle(_translate("HSG", "Form", None))
        self.groupBox_42.setTitle(_translate("HSG", "Sample", None))
        self.groupBox_4.setTitle(_translate("HSG", "NIR Power (mW)", None))
        self.tCCDNIRP.setText(_translate("HSG", "0", None))
        self.bCCDBack.setText(_translate("HSG", "Take Background", None))
        self.groupBox_35.setTitle(_translate("HSG", "Gain", None))
        self.tEMCCDGain.setText(_translate("HSG", "1", None))
        self.groupBox_38.setTitle(_translate("HSG", "Bg Number", None))
        self.tCCDBGNum.setText(_translate("HSG", "0", None))
        self.bCCDImage.setText(_translate("HSG", "Take Image", None))
        self.groupBox_34.setTitle(_translate("HSG", "Exposure (s)", None))
        self.tEMCCDExp.setText(_translate("HSG", "0.5", None))
        self.groupBox_36.setTitle(_translate("HSG", "NIR Wl (nm)", None))
        self.tCCDNIRwavelength.setText(_translate("HSG", "0", None))
        self.groupBox_37.setTitle(_translate("HSG", "Image Number", None))
        self.tCCDImageNum.setText(_translate("HSG", "0", None))
        self.groupBox_40.setTitle(_translate("HSG", "FEL Energy (mJ)", None))
        self.tCCDFELP.setText(_translate("HSG", "0", None))
        self.groupBox_59.setTitle(_translate("HSG", "E (kV/cm)", None))
        self.tCCDEField.setText(_translate("HSG", "0.0", None))
        self.groupBox_60.setTitle(_translate("HSG", "I (kW/cm2)", None))
        self.tCCDIntensity.setText(_translate("HSG", "0.0", None))
        self.groupBox_Series.setTitle(_translate("HSG", "Series", None))
        self.tCCDSeries.setToolTip(_translate("HSG", "NIRP, NIRW, FELF, FELP, SLITS, SPECL", None))
        self.groupBox.setTitle(_translate("HSG", "Spectrum step", None))
        self.groupBox_46.setTitle(_translate("HSG", "Comments", None))
        self.tabWidget_3.setTabText(self.tabWidget_3.indexOf(self.tab_3), _translate("HSG", "Main Settings", None))
        self.groupBox_55.setTitle(_translate("HSG", "Spot Size(cm)", None))
        self.tCCDSpotSize.setToolTip(_translate("HSG", "Radius of FEL spot size", None))
        self.tCCDSpotSize.setText(_translate("HSG", "0.05", None))
        self.groupBox_45.setTitle(_translate("HSG", "Slits", None))
        self.tCCDSlits.setText(_translate("HSG", "0", None))
        self.groupBox_39.setTitle(_translate("HSG", "FEL Freq (cm-1)", None))
        self.tCCDFELFreq.setText(_translate("HSG", "0", None))
        self.groupBox_58.setTitle(_translate("HSG", "Sample E_eff", None))
        self.tCCDEffectiveField.setText(_translate("HSG", "1.0", None))
        self.groupBox_2.setTitle(_translate("HSG", "Sample Temp", None))
        self.groupBox_57.setTitle(_translate("HSG", "Window Trans", None))
        self.tCCDWindowTransmission.setText(_translate("HSG", "1.0", None))
        self.groupBox_44.setTitle(_translate("HSG", "Ymax", None))
        self.tCCDYMax.setText(_translate("HSG", "400", None))
        self.groupBox_43.setTitle(_translate("HSG", "Ymin", None))
        self.tCCDYMin.setText(_translate("HSG", "0", None))
        self.groupBox_41.setTitle(_translate("HSG", "Rep Rate (Hz)", None))
        self.tCCDFELRR.setText(_translate("HSG", "0.75", None))
        self.groupBox_3.setTitle(_translate("HSG", "FEL Pol", None))
        self.groupBox_5.setTitle(_translate("HSG", "NIR Pol", None))
        self.tabWidget_3.setTabText(self.tabWidget_3.indexOf(self.tab_4), _translate("HSG", "Other Settings", None))
        self.lCCDProg.setText(_translate("HSG", "Done.", None))
        self.groupBox_56.setTitle(_translate("HSG", "SB #", None))
        self.tCCDSidebandNumber.setText(_translate("HSG", "1", None))
        self.groupBox_54.setTitle(_translate("HSG", "FEL Pulses", None))

from ImageViewWithPlotItemContainer import ImageViewWithPlotItemContainer
from InstsAndQt.customQt import QFNumberEdit, QINumberEdit
from pyqtgraph import PlotWidget
