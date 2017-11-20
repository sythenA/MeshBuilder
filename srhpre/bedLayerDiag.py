
import os
import os.path
from PyQt4 import uic
from PyQt4.QtGui import QDialog


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'bedLayerDiag.ui'))


class bedLayerDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(bedLayerDialog, self).__init__(parent)
        self.setupUi(self)
