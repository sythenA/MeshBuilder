# -*- coding: big5 -*-

import os
import os.path
from PyQt4.QtCore import QSettings, qVersion, QTranslator, QCoreApplication
from shepredDialog import shepredDialog
from commonDialog import criticalBox, warningBox
from commonDialog import fileBrowser, folderBrowser, saveFileBrowser


class shepred:
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'meshBuilder_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.dlg = shepredDialog()
        self.projFolder = os.path.expanduser("~")

    def run(self):
        meshFileCaption = u'請選擇輸入網格(.2dm格式)'
        self.dlg.pbtnFileSelector.clicked.connect(lambda: fileBrowser(self.dlg,
            meshFileCaption, self.projFolder, self.dlg.lineEditMeshFileName,
            presetType='.2dm'))

        result = self.dlg.exec_()
        if result:
            pass
