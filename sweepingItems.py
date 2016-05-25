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
        self.dialog = ParamChooser()

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




class ParamChoices(QtGui.QComboBox):
    def __init__(self, parent=None, *args, **kwargs):
        super(ParamChoices, self).__init__(parent)
        actions = [
            "---CCD---",
            "AD Channel",
            "VSS",
            "HSS",
            "Trigger"
        ]

        self.addItems(actions)
        # for act in actions:
        #     self.addAction(act)
        #     self.add


class ParamChooser(QtGui.QDialog):
    def __init__(self, parent = None, *args, **kwargs):
        super(ParamChooser, self).__init__(parent)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        headerView = self.ui.tableWidget.horizontalHeader()
        headerView.setResizeMode(QtGui.QHeaderView.Stretch)
        # headerView.setResizeMode(1, QtGui.QHeaderView.Interactive)
        headerView.setResizeMode(0, QtGui.QHeaderView.Interactive)
        self.addNewRow()


        self.show()

    def addNewRow(self):
        self.ui.tableWidget.insertRow(self.ui.tableWidget.rowCount())
        self.ui.tableWidget.setCellWidget(self.ui.tableWidget.rowCount()-1, 0,
                                          ParamChoices())




