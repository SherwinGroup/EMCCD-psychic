# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\dvalovcin\Documents\GitHub\EMCCD-psychic\UIs\PL.ui'
#
# Created: Mon Apr 27 16:23:41 2015
#      by: PyQt4 UI code generator 4.9.6
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

class Ui_PL(object):
    def setupUi(self, PL):
        PL.setObjectName(_fromUtf8("PL"))
        PL.resize(924, 751)
        self.verticalLayout = QtGui.QVBoxLayout(PL)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.splitterAll = QtGui.QSplitter(PL)
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
        self.horizontalLayout_49 = QtGui.QHBoxLayout(self.tab_3)
        self.horizontalLayout_49.setObjectName(_fromUtf8("horizontalLayout_49"))
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
        self.tCCDSeries = QtGui.QLineEdit(self.groupBox_42)
        self.tCCDSeries.setStatusTip(_fromUtf8(""))
        self.tCCDSeries.setWhatsThis(_fromUtf8(""))
        self.tCCDSeries.setAccessibleName(_fromUtf8(""))
        self.tCCDSeries.setAccessibleDescription(_fromUtf8(""))
        self.tCCDSeries.setInputMethodHints(QtCore.Qt.ImhNone)
        self.tCCDSeries.setText(_fromUtf8(""))
        self.tCCDSeries.setObjectName(_fromUtf8("tCCDSeries"))
        self.gridLayout_12.addWidget(self.tCCDSeries, 0, 0, 1, 1)
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
        self.gridLayout.addWidget(self.bCCDBack, 4, 0, 1, 1)
        self.groupBox_35 = QtGui.QGroupBox(self.tab_3)
        self.groupBox_35.setFlat(True)
        self.groupBox_35.setObjectName(_fromUtf8("groupBox_35"))
        self.horizontalLayout_33 = QtGui.QHBoxLayout(self.groupBox_35)
        self.horizontalLayout_33.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_33.setObjectName(_fromUtf8("horizontalLayout_33"))
        self.tEMCCDGain = QINumberEdit(self.groupBox_35)
        self.tEMCCDGain.setObjectName(_fromUtf8("tEMCCDGain"))
        self.horizontalLayout_33.addWidget(self.tEMCCDGain)
        self.gridLayout.addWidget(self.groupBox_35, 4, 1, 1, 1)
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
        self.gridLayout.addWidget(self.groupBox_38, 4, 2, 1, 1)
        self.bCCDImage = QtGui.QPushButton(self.tab_3)
        self.bCCDImage.setObjectName(_fromUtf8("bCCDImage"))
        self.gridLayout.addWidget(self.bCCDImage, 3, 0, 1, 1)
        self.groupBox_34 = QtGui.QGroupBox(self.tab_3)
        self.groupBox_34.setFlat(True)
        self.groupBox_34.setObjectName(_fromUtf8("groupBox_34"))
        self.horizontalLayout_32 = QtGui.QHBoxLayout(self.groupBox_34)
        self.horizontalLayout_32.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_32.setObjectName(_fromUtf8("horizontalLayout_32"))
        self.tEMCCDExp = QFNumberEdit(self.groupBox_34)
        self.tEMCCDExp.setObjectName(_fromUtf8("tEMCCDExp"))
        self.horizontalLayout_32.addWidget(self.tEMCCDExp)
        self.gridLayout.addWidget(self.groupBox_34, 3, 1, 1, 1)
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
        self.gridLayout.addWidget(self.groupBox_37, 3, 2, 1, 1)
        self.gridLayout.setColumnStretch(0, 1)
        self.verticalLayout_9.addLayout(self.gridLayout)
        self.groupBox_46 = QtGui.QGroupBox(self.tab_3)
        self.groupBox_46.setFlat(True)
        self.groupBox_46.setObjectName(_fromUtf8("groupBox_46"))
        self.horizontalLayout_37 = QtGui.QHBoxLayout(self.groupBox_46)
        self.horizontalLayout_37.setObjectName(_fromUtf8("horizontalLayout_37"))
        self.tCCDComments = QtGui.QTextEdit(self.groupBox_46)
        self.tCCDComments.setObjectName(_fromUtf8("tCCDComments"))
        self.horizontalLayout_37.addWidget(self.tCCDComments)
        self.verticalLayout_9.addWidget(self.groupBox_46)
        self.verticalLayout_9.setStretch(1, 1)
        self.horizontalLayout_49.addLayout(self.verticalLayout_9)
        self.tabWidget_3.addTab(self.tab_3, _fromUtf8(""))
        self.tab_4 = QtGui.QWidget()
        self.tab_4.setObjectName(_fromUtf8("tab_4"))
        self.horizontalLayout_52 = QtGui.QHBoxLayout(self.tab_4)
        self.horizontalLayout_52.setObjectName(_fromUtf8("horizontalLayout_52"))
        self.gridLayout_17 = QtGui.QGridLayout()
        self.gridLayout_17.setObjectName(_fromUtf8("gridLayout_17"))
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
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_17.addItem(spacerItem, 2, 0, 1, 1)
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
        self.gCCDImage = GraphicsLayoutWidget(self.splitterImages)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.gCCDImage.sizePolicy().hasHeightForWidth())
        self.gCCDImage.setSizePolicy(sizePolicy)
        self.gCCDImage.setObjectName(_fromUtf8("gCCDImage"))
        self.gCCDBack = GraphicsLayoutWidget(self.splitterImages)
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
        self.horizontalLayout_34.setStretch(0, 9)
        self.horizontalLayout_34.setStretch(1, 1)
        self.horizontalLayout_34.setStretch(2, 1)
        self.verticalLayout.addWidget(self.splitterAll)

        self.retranslateUi(PL)
        self.tabWidget_3.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(PL)

    def retranslateUi(self, PL):
        PL.setWindowTitle(_translate("PL", "Form", None))
        self.groupBox_42.setTitle(_translate("PL", "Series", None))
        self.tCCDSeries.setToolTip(_translate("PL", "NIRP, NIRW, FELF, FELP, SLITS, SPECL", None))
        self.groupBox_4.setTitle(_translate("PL", "NIR Power (mW)", None))
        self.tCCDNIRP.setText(_translate("PL", "0", None))
        self.bCCDBack.setText(_translate("PL", "Take Background", None))
        self.groupBox_35.setTitle(_translate("PL", "Gain", None))
        self.tEMCCDGain.setText(_translate("PL", "1", None))
        self.groupBox_38.setTitle(_translate("PL", "Bg Number", None))
        self.tCCDBGNum.setText(_translate("PL", "0", None))
        self.bCCDImage.setText(_translate("PL", "Take Image", None))
        self.groupBox_34.setTitle(_translate("PL", "Exposure (s)", None))
        self.tEMCCDExp.setText(_translate("PL", "0.5", None))
        self.groupBox_36.setTitle(_translate("PL", "NIR Wl (nm)", None))
        self.tCCDNIRwavelength.setText(_translate("PL", "0", None))
        self.groupBox_37.setTitle(_translate("PL", "Image Number", None))
        self.tCCDImageNum.setText(_translate("PL", "0", None))
        self.groupBox_46.setTitle(_translate("PL", "Comments", None))
        self.tabWidget_3.setTabText(self.tabWidget_3.indexOf(self.tab_3), _translate("PL", "Main Settings", None))
        self.groupBox_2.setTitle(_translate("PL", "Sample Temp", None))
        self.groupBox_44.setTitle(_translate("PL", "Ymax", None))
        self.tCCDYMax.setText(_translate("PL", "400", None))
        self.groupBox_45.setTitle(_translate("PL", "Slits", None))
        self.tCCDSlits.setText(_translate("PL", "0", None))
        self.groupBox_43.setTitle(_translate("PL", "Ymin", None))
        self.tCCDYMin.setText(_translate("PL", "0", None))
        self.tabWidget_3.setTabText(self.tabWidget_3.indexOf(self.tab_4), _translate("PL", "Other Settings", None))
        self.lCCDProg.setText(_translate("PL", "Done.", None))

from pyqtgraph import PlotWidget, GraphicsLayoutWidget
from InstsAndQt.customQt import QINumberEdit, QFNumberEdit
