# -*- coding: big5 -*-

import os
from PyQt4 import QtGui, uic
from commonDialog import fileBrowser


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'MeshSelector.ui'))


class meshSelectorDiag(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(meshSelectorDiag, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)


class meshSelector:
    def __init__(self, iface, projFolder):
        self.iface = iface

        self.dlg = meshSelectorDiag()

        caption = u'�п�ܤ@��.2dm�ɮ�'
        self.dlg.where2dmBtn.clicked.connect(
            lambda: fileBrowser(self.dlg, caption, projFolder,
                                self.dlg.where2dmEdit, '(*.2dm)'))
        self.dlg.where2dmBtn.setToolTip(caption)
        caption2 = u'�п�ܻP�ҿ�.2dm�ɮ׹�����.msh�ɮ�(Ū�����ϦW�٥�)'
        self.dlg.whereMshBtn.clicked.connect(
            lambda: fileBrowser(self.dlg, caption2, projFolder,
                                self.dlg.whereMshEdit, '(*.msh)'))

    def run(self):
        result = self.dlg.exec_()
        if result:
            self.mesh2dm = self.dlg.where2dmEdit.text()
            self.meshMsh = self.dlg.whereMshEdit.text()
            return result
