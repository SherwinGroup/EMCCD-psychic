# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\dvalovcin\Documents\GitHub\EMCCD-psychic\UIs\Oscilloscope.ui'
#
# Created: Mon Nov 23 11:48:06 2015
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtCore.QCoreApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtCore.QCoreApplication.translate(context, text, disambig)

class Ui_Oscilloscope(object):
    def setupUi(self, Oscilloscope):
        Oscilloscope.setObjectName("Oscilloscope")
        Oscilloscope.resize(741, 543)
        self.verticalLayout = QtWidgets.QVBoxLayout(Oscilloscope)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gOsc = PlotWidget(Oscilloscope)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.gOsc.sizePolicy().hasHeightForWidth())
        self.gOsc.setSizePolicy(sizePolicy)
        self.gOsc.setObjectName("gOsc")
        self.verticalLayout.addWidget(self.gOsc)
        self.tabWidget_2 = QtWidgets.QTabWidget(Oscilloscope)
        self.tabWidget_2.setObjectName("tabWidget_2")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.tab)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.gridLayout_5 = QtWidgets.QGridLayout()
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.groupBox_25 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_25.setFlat(True)
        self.groupBox_25.setObjectName("groupBox_25")
        self.horizontalLayout_23 = QtWidgets.QHBoxLayout(self.groupBox_25)
        self.horizontalLayout_23.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_23.setObjectName("horizontalLayout_23")
        self.tBgSt = QFNumberEdit(self.groupBox_25)
        self.tBgSt.setText("")
        self.tBgSt.setObjectName("tBgSt")
        self.horizontalLayout_23.addWidget(self.tBgSt)
        self.gridLayout_5.addWidget(self.groupBox_25, 0, 0, 1, 1)
        self.groupBox_27 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_27.setFlat(True)
        self.groupBox_27.setObjectName("groupBox_27")
        self.horizontalLayout_25 = QtWidgets.QHBoxLayout(self.groupBox_27)
        self.horizontalLayout_25.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_25.setObjectName("horizontalLayout_25")
        self.tFpSt = QFNumberEdit(self.groupBox_27)
        self.tFpSt.setObjectName("tFpSt")
        self.horizontalLayout_25.addWidget(self.tFpSt)
        self.gridLayout_5.addWidget(self.groupBox_27, 0, 1, 1, 1)
        self.groupBox_29 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_29.setFlat(True)
        self.groupBox_29.setObjectName("groupBox_29")
        self.horizontalLayout_27 = QtWidgets.QHBoxLayout(self.groupBox_29)
        self.horizontalLayout_27.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_27.setObjectName("horizontalLayout_27")
        self.tCdSt = QFNumberEdit(self.groupBox_29)
        self.tCdSt.setObjectName("tCdSt")
        self.horizontalLayout_27.addWidget(self.tCdSt)
        self.gridLayout_5.addWidget(self.groupBox_29, 0, 2, 1, 1)
        self.groupBox_26 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_26.setFlat(True)
        self.groupBox_26.setObjectName("groupBox_26")
        self.horizontalLayout_24 = QtWidgets.QHBoxLayout(self.groupBox_26)
        self.horizontalLayout_24.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_24.setObjectName("horizontalLayout_24")
        self.tBgEn = QFNumberEdit(self.groupBox_26)
        self.tBgEn.setText("")
        self.tBgEn.setObjectName("tBgEn")
        self.horizontalLayout_24.addWidget(self.tBgEn)
        self.gridLayout_5.addWidget(self.groupBox_26, 1, 0, 1, 1)
        self.groupBox_28 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_28.setFlat(True)
        self.groupBox_28.setObjectName("groupBox_28")
        self.horizontalLayout_26 = QtWidgets.QHBoxLayout(self.groupBox_28)
        self.horizontalLayout_26.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_26.setObjectName("horizontalLayout_26")
        self.tFpEn = QFNumberEdit(self.groupBox_28)
        self.tFpEn.setObjectName("tFpEn")
        self.horizontalLayout_26.addWidget(self.tFpEn)
        self.gridLayout_5.addWidget(self.groupBox_28, 1, 1, 1, 1)
        self.groupBox_30 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_30.setFlat(True)
        self.groupBox_30.setObjectName("groupBox_30")
        self.horizontalLayout_28 = QtWidgets.QHBoxLayout(self.groupBox_30)
        self.horizontalLayout_28.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_28.setObjectName("horizontalLayout_28")
        self.tCdEn = QFNumberEdit(self.groupBox_30)
        self.tCdEn.setObjectName("tCdEn")
        self.horizontalLayout_28.addWidget(self.tCdEn)
        self.gridLayout_5.addWidget(self.groupBox_30, 1, 2, 1, 1)
        self.bOscInit = QtWidgets.QPushButton(self.tab)
        self.bOscInit.setObjectName("bOscInit")
        self.gridLayout_5.addWidget(self.bOscInit, 0, 3, 1, 1)
        self.horizontalLayout_4.addLayout(self.gridLayout_5)
        self.tabWidget_2.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.horizontalLayout_48 = QtWidgets.QHBoxLayout(self.tab_2)
        self.horizontalLayout_48.setObjectName("horizontalLayout_48")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.groupBox_53 = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox_53.setFlat(True)
        self.groupBox_53.setObjectName("groupBox_53")
        self.horizontalLayout_47 = QtWidgets.QHBoxLayout(self.groupBox_53)
        self.horizontalLayout_47.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_47.setObjectName("horizontalLayout_47")
        self.tOscCDRatio = QFNumberEdit(self.groupBox_53)
        self.tOscCDRatio.setObjectName("tOscCDRatio")
        self.horizontalLayout_47.addWidget(self.tOscCDRatio)
        self.gridLayout.addWidget(self.groupBox_53, 0, 2, 1, 1)
        self.groupBox_52 = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox_52.setFlat(True)
        self.groupBox_52.setObjectName("groupBox_52")
        self.horizontalLayout_46 = QtWidgets.QHBoxLayout(self.groupBox_52)
        self.horizontalLayout_46.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_46.setObjectName("horizontalLayout_46")
        self.tOscFPRatio = QFNumberEdit(self.groupBox_52)
        self.tOscFPRatio.setObjectName("tOscFPRatio")
        self.horizontalLayout_46.addWidget(self.tOscFPRatio)
        self.gridLayout.addWidget(self.groupBox_52, 0, 1, 1, 1)
        self.groupBox_10 = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox_10.setFlat(True)
        self.groupBox_10.setObjectName("groupBox_10")
        self.horizontalLayout_45 = QtWidgets.QHBoxLayout(self.groupBox_10)
        self.horizontalLayout_45.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_45.setObjectName("horizontalLayout_45")
        self.tOscPulses = QtWidgets.QLineEdit(self.groupBox_10)
        self.tOscPulses.setEnabled(False)
        self.tOscPulses.setObjectName("tOscPulses")
        self.horizontalLayout_45.addWidget(self.tOscPulses)
        self.gridLayout.addWidget(self.groupBox_10, 0, 0, 1, 1)
        self.groupBox = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox.setFlat(True)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.groupBox)
        self.horizontalLayout_2.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.cPyroMode = QtWidgets.QComboBox(self.groupBox)
        self.cPyroMode.setObjectName("cPyroMode")
        self.cPyroMode.addItem("")
        self.cPyroMode.addItem("")
        self.horizontalLayout_2.addWidget(self.cPyroMode)
        self.gridLayout.addWidget(self.groupBox, 1, 0, 1, 1)
        self.groupBox_2 = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox_2.setFlat(True)
        self.groupBox_2.setObjectName("groupBox_2")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_3.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.cFELCoupler = QtWidgets.QComboBox(self.groupBox_2)
        self.cFELCoupler.setObjectName("cFELCoupler")
        self.cFELCoupler.addItem("")
        self.cFELCoupler.addItem("")
        self.horizontalLayout_3.addWidget(self.cFELCoupler)
        self.gridLayout.addWidget(self.groupBox_2, 1, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 3, 1, 1)
        self.horizontalLayout_48.addLayout(self.gridLayout)
        self.tabWidget_2.addTab(self.tab_2, "")
        self.verticalLayout.addWidget(self.tabWidget_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.bOPause = QtWidgets.QPushButton(Oscilloscope)
        self.bOPause.setCheckable(True)
        self.bOPause.setChecked(True)
        self.bOPause.setObjectName("bOPause")
        self.horizontalLayout.addWidget(self.bOPause)
        self.groupBox_31 = QtWidgets.QGroupBox(Oscilloscope)
        self.groupBox_31.setFlat(True)
        self.groupBox_31.setObjectName("groupBox_31")
        self.horizontalLayout_29 = QtWidgets.QHBoxLayout(self.groupBox_31)
        self.horizontalLayout_29.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_29.setObjectName("horizontalLayout_29")
        self.cOGPIB = QtWidgets.QComboBox(self.groupBox_31)
        self.cOGPIB.setObjectName("cOGPIB")
        self.horizontalLayout_29.addWidget(self.cOGPIB)
        self.horizontalLayout.addWidget(self.groupBox_31)
        self.groupBox_32 = QtWidgets.QGroupBox(Oscilloscope)
        self.groupBox_32.setFlat(True)
        self.groupBox_32.setObjectName("groupBox_32")
        self.horizontalLayout_30 = QtWidgets.QHBoxLayout(self.groupBox_32)
        self.horizontalLayout_30.setContentsMargins(0, 10, 0, 0)
        self.horizontalLayout_30.setObjectName("horizontalLayout_30")
        self.cOChannel = QtWidgets.QComboBox(self.groupBox_32)
        self.cOChannel.setObjectName("cOChannel")
        self.cOChannel.addItem("")
        self.cOChannel.addItem("")
        self.cOChannel.addItem("")
        self.cOChannel.addItem("")
        self.horizontalLayout_30.addWidget(self.cOChannel)
        self.horizontalLayout.addWidget(self.groupBox_32)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.bOPop = QtWidgets.QPushButton(Oscilloscope)
        self.bOPop.setObjectName("bOPop")
        self.horizontalLayout.addWidget(self.bOPop)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Oscilloscope)
        self.tabWidget_2.setCurrentIndex(0)
        self.cPyroMode.setCurrentIndex(1)
        self.cOChannel.setCurrentIndex(2)
        QtCore.QMetaObject.connectSlotsByName(Oscilloscope)

    def retranslateUi(self, Oscilloscope):
        Oscilloscope.setWindowTitle(_translate("Oscilloscope", "Form", None))
        self.groupBox_25.setTitle(_translate("Oscilloscope", "Background Start", None))
        self.groupBox_27.setTitle(_translate("Oscilloscope", "Front Porch Start", None))
        self.groupBox_29.setTitle(_translate("Oscilloscope", "Cavity Dump Start", None))
        self.groupBox_26.setTitle(_translate("Oscilloscope", "Background End", None))
        self.groupBox_28.setTitle(_translate("Oscilloscope", "Front Porch End", None))
        self.groupBox_30.setTitle(_translate("Oscilloscope", "Cavity Dump End", None))
        self.bOscInit.setText(_translate("Oscilloscope", "Initialize Regions", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab), _translate("Oscilloscope", "Boxcar Regions", None))
        self.groupBox_53.setTitle(_translate("Oscilloscope", "CD Ratio", None))
        self.tOscCDRatio.setText(_translate("Oscilloscope", "5", None))
        self.groupBox_52.setTitle(_translate("Oscilloscope", "FP Ratio", None))
        self.tOscFPRatio.setText(_translate("Oscilloscope", "1", None))
        self.groupBox_10.setTitle(_translate("Oscilloscope", "No. Pulses", None))
        self.groupBox.setTitle(_translate("Oscilloscope", "Pyro Mode", None))
        self.cPyroMode.setItemText(0, _translate("Oscilloscope", "Instant", None))
        self.cPyroMode.setItemText(1, _translate("Oscilloscope", "Integrating", None))
        self.groupBox_2.setTitle(_translate("Oscilloscope", "Coupler", None))
        self.cFELCoupler.setItemText(0, _translate("Oscilloscope", "Cavity Dump", None))
        self.cFELCoupler.setItemText(1, _translate("Oscilloscope", "Hole", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_2), _translate("Oscilloscope", "Pulse Counting Settings", None))
        self.bOPause.setText(_translate("Oscilloscope", "Pause", None))
        self.groupBox_31.setTitle(_translate("Oscilloscope", "GPIB", None))
        self.cOGPIB.setToolTip(_translate("Oscilloscope", "GPIB0::5::INSTR", None))
        self.groupBox_32.setTitle(_translate("Oscilloscope", "Channel", None))
        self.cOChannel.setItemText(0, _translate("Oscilloscope", "1", None))
        self.cOChannel.setItemText(1, _translate("Oscilloscope", "2", None))
        self.cOChannel.setItemText(2, _translate("Oscilloscope", "3", None))
        self.cOChannel.setItemText(3, _translate("Oscilloscope", "4", None))
        self.bOPop.setText(_translate("Oscilloscope", "Pop Out", None))

from pyqtgraph import PlotWidget

from InstsAndQt.customQt import QFNumberEdit

