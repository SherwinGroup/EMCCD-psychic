from PyQt4 import QtGui, QtCore
from sweepingItems import *
from UIs.sweepSelector_ui import Ui_Dialog

def doubleclicker(listItem):
    """

    :param listItem:
    :type listItem: SetterBase
    :return:
    """
    print "double clicked"
    print listItem.text()
    listItem.changeAction()

def clicked(*args, **kwargs):
    print args, kwargs


class SweepSelector(QtGui.QDialog):
    def __init__(self, *args, **kwargs):
        print "init sweepselector", args, kwargs
        super(SweepSelector, self).__init__()

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.addItem = self.ui.listActions.addItem
        self.itemDoubleClicked = self.ui.listActions.itemDoubleClicked
        self.itemClicked = self.ui.listActions.itemClicked

        self.show()


if __name__ == '__main__':
    import sys
    ex = QtGui.QApplication([])
    a = SweepSelector()
    a.itemDoubleClicked.connect(doubleclicker)
    a.itemClicked.connect(clicked)
    c = SetterParam()
    a.addItem(c)
    print "preinted"
    sys.exit(ex.exec_())