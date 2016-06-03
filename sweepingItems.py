from PyQt4 import QtGui, QtCore
from CCDMain import CCDWindow
from UIs.parameterChanger_ui import Ui_Dialog

class SetterBase(QtGui.QListWidgetItem):
    def __init__(self, parent=None):
        """

        :param parent: Parent CCD window which
            all actions will be done on
        :type parent: CCDWindow
        """
        super(SetterBase, self).__init__()
        self.setText(self.getTextDesc())

    def getTextDesc(self):
        """
        Get the text to describe what this
        action will do for listing
        :return:
        """
        return "Null Action"

    def doAction(self):
        """
        Do whatever action is desired to the
        CCD window.
        :return:
        """
        pass

    def changeAction(self):
        """
        Called when the item in the list is double clicked.
        Should do what is required to figure out
        how to set the necessary parameters for setting
        the action (what paremeters to change, files to load,
        exposure to take)
        :return:
        """
        pass

class SetterParam(SetterBase):
    """
    For setting parameters (NIRL, FEL settings).
    Simple things which are held in the text edits
    """
    def changeAction(self):
        self.dialog = ParamChooser(self.listWidget())

class SetterTakeImage(SetterBase):
    """
    Take image. Should define number of images,
    type (image, back, ref), to process after taking,
    to prompt for confirmation
    """
    pass

class SetterLoadBackground(SetterBase):
    """
    Action to load a background file. Needs to prompt
    which files to load and pass them to curexp
    """
    pass

class SetterLoadReference(SetterBase):
    """
    Action to load a reference file. Needs to prompt
    which files to load and pass them to curexp
    """
    pass

class SetterPause(SetterBase):
    """
    Prompt for a pause or user action for things
    which aren't automated
    """
    pass



class ParamChoices(QtGui.QComboBox):
    def __init__(self, parent=None, *args, **kwargs):
        super(ParamChoices, self).__init__(parent)
        actions = [
            "---CCD---",
            # "AD Channel",
            # "VSS",
            # "Read Mode",
            # "HSS",
            "Trigger",
            # "Acquisition Mode",
            "Shutter",
            "Vertical Binning",
            "Vertical Start",
            "Vertical End"
            "Temperature",
            "Exposure",
            "Gain",
            "---Exp---",
            "NIR Wavelength",
            "NIR Power",
            "Sample",
            "Image Number",
            "Background Number",
            "Series",
            "Spec Step",
            "Comments",
            "NIR Polarization",
            "Slits",
            "Sample Temp",
            "YMin",
            "YMax",
            "---FEL---",
            "Energy",
            "Frequency",
            "Spot Size",
            "Window Trans",
            "Effective Field",
            "---SPEC---",
            "Wavelength",
            "Grating",
            "---ROTS---",
            "THz Attenuator",
            "Newport Axis 1"
        ]

        self.addItems(actions)
        # for act in actions:
        #     self.addAction(act)
        #     self.add


class ParamChooser(QtGui.QDialog):
    def __init__(self, parent = None, *args, **kwargs):
        super(ParamChooser, self).__init__(parent)
        self.setModal(True)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        headerView = self.ui.tableWidget.horizontalHeader()
        headerView.setResizeMode(QtGui.QHeaderView.Stretch)
        headerView.setResizeMode(0, QtGui.QHeaderView.Interactive)
        self.addNewRow()


        self.show()

    def addNewRow(self):
        self.ui.tableWidget.insertRow(self.ui.tableWidget.rowCount())
        pc = ParamChoices()
        pc.currentIndexChanged.connect(self.changeEditorDelegate)
        self.ui.tableWidget.setCellWidget(self.ui.tableWidget.rowCount()-1, 0,
                                          pc)
    def getWidgetLocation(self, widget):
        for row in range(self.ui.tableWidget.rowCount()):
            if widget is self.ui.tableWidget.cellWidget(row, 0):
                return row

        return -1

    def changeEditorDelegate(self, word):
        senderRow = self.getWidgetLocation(self.sender())
        text = self.sender().currentText()
        if "---" in text:
            self.ui.tableWidget.removeCellWidget(senderRow, 1)
            print self.ui.tableWidget.item(senderRow, 1)

        else:
            self.ui.tableWidget.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers)
        if senderRow == self.ui.tableWidget.rowCount()-1:
            self.addNewRow()




