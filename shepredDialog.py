
import os
import os.path
from PyQt4 import uic
from PyQt4.QtGui import QDialog, QPixmap


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'srhpre.ui'))


class shepredDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(shepredDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.projFolder = ''

    def closeEvent(self, event):
        self.lineEditCaseName.clear()
        self.lineEditDescription.clear()
        self.lineEditMeshFileName.clear()
        self.lineMeshFilePath.clear()
        self.lineEditTStep.clear()
        self.lineEditTTotal.clear()
        self.turbParaInput.clear()
        self.mannTable.clear()
        self.InitCondTable.clear()
        self.OutIntvTable.clear()
        self.boundaryTable.clear()

        self.accept()
        self.close()
        return QDialog.closeEvent(self, event)
