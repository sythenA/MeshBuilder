
import os
from PyQt4 import QtGui, uic


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'meshLoadSelector.ui'))


class selectorDiag(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(selectorDiag, self).__init__(parent)

        self.setupUi(self)


class loadSelector:
    def __init__(self, iface, title):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        self.dlg = selectorDiag()
        self.dlg.setWindowTitle(title)
        self.dlg.loadBtn.clicked.connect(self.loadOld)
        self.dlg.makeNewBtn.clicked.connect(self.newShpLayers)

    def newShpLayers(self):
        self.dlg.done(1)

    def loadOld(self):
        self.dlg.reject()

    def run(self):
        result = self.dlg.exec_()
        if result:
            return result
