# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'sweepSelector.ui'
#
# Created: Mon May 23 21:32:45 2016
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

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(552, 499)
        self.horizontalLayout = QtGui.QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.listActions = QtGui.QListWidget(Dialog)
        self.listActions.setObjectName(_fromUtf8("listActions"))
        self.horizontalLayout.addWidget(self.listActions)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.bAdd = QtGui.QPushButton(Dialog)
        self.bAdd.setObjectName(_fromUtf8("bAdd"))
        self.verticalLayout.addWidget(self.bAdd)
        self.bRemove = QtGui.QPushButton(Dialog)
        self.bRemove.setObjectName(_fromUtf8("bRemove"))
        self.verticalLayout.addWidget(self.bRemove)
        self.bUp = QtGui.QPushButton(Dialog)
        self.bUp.setObjectName(_fromUtf8("bUp"))
        self.verticalLayout.addWidget(self.bUp)
        self.bDown = QtGui.QPushButton(Dialog)
        self.bDown.setObjectName(_fromUtf8("bDown"))
        self.verticalLayout.addWidget(self.bDown)
        self.bSave = QtGui.QPushButton(Dialog)
        self.bSave.setObjectName(_fromUtf8("bSave"))
        self.verticalLayout.addWidget(self.bSave)
        self.bLoad = QtGui.QPushButton(Dialog)
        self.bLoad.setObjectName(_fromUtf8("bLoad"))
        self.verticalLayout.addWidget(self.bLoad)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.bOk = QtGui.QPushButton(Dialog)
        self.bOk.setObjectName(_fromUtf8("bOk"))
        self.verticalLayout.addWidget(self.bOk)
        self.bCancel = QtGui.QPushButton(Dialog)
        self.bCancel.setObjectName(_fromUtf8("bCancel"))
        self.verticalLayout.addWidget(self.bCancel)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.bAdd.setText(_translate("Dialog", "Add Item", None))
        self.bRemove.setText(_translate("Dialog", "Remove Item", None))
        self.bUp.setText(_translate("Dialog", "Move Up", None))
        self.bDown.setText(_translate("Dialog", "Move Down", None))
        self.bSave.setText(_translate("Dialog", "Save...", None))
        self.bLoad.setText(_translate("Dialog", "Load...", None))
        self.bOk.setText(_translate("Dialog", "OK", None))
        self.bCancel.setText(_translate("Dialog", "Cancel", None))

