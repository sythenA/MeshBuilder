
import os
import os.path
from PyQt4 import uic
from PyQt4.QtGui import QDialog
from PyQt4.QtCore import QSettings, QTranslator


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'QuasiSediment.ui'))


class quasiSediDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(quasiSediDialog, self).__init__(parent)
        self.setupUi(self)


class quasiSedimentSetting:
    def __init__(self, iface, interval, dt):
        self.iface = iface

        locale = QSettings().value('locale/userLocale')[0:2]
        self.plugin_dir = os.path.dirname(__file__)
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'meshBuilder_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

        self.dlg = quasiSediDialog()

        if interval:
            self.dlg.timeIntervalEdit.setText(str(interval))
        if dt:
            self.dlg.dtEdit.setText(str(dt))

    def run(self):
        result = self.dlg.exec_()

        if result:
            return self.dlg.timeIntervalEdit.text(), self.dlg.dtEdit.text()
