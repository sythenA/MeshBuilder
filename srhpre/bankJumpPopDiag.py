import os
from PyQt4 import uic
from PyQt4.QtGui import QDialog
from commonDialog import onCritical


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'bankJumpPop.ui'))


class bankJumpPopDiag(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(bankJumpPopDiag, self).__init__(parent)
        self.setupUi(self)


class setBankJump:
    def __init__(self, iface):
        self.iface = iface
        self.dlg = bankJumpPopDiag(parent=iface.mainWindow())

    def run(self):
        result = self.dlg.exec_()
        if result == 1:
            return [int(self.dlg.nJumpEdit.text()),
                    int(self.dlg.nLayersEdit.text())]
        else:
            onCritical(303)
