# -*- coding: big5 -*-

import os
import os.path
from PyQt4 import uic
from PyQt4.QtGui import QDialog, QTableWidgetItem, QComboBox, QIcon, QPixmap


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'zoneSeq.ui'))


class zoneSeqDiag(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(zoneSeqDiag, self).__init__(parent)
        self.setupUi(self)


class zoneSeqIterator:
    def __init__(self, iface, zoneOrd, parentDiag):

        self.plugin_dir = os.path.dirname(__file__)
        self.iface = iface
        self.zoneOrd = zoneOrd
        self.parentDlg = parentDiag

        self.dlg = zoneSeqDiag()
        self.setTable()

        upPix = QPixmap(os.path.join(self.plugin_dir,
                                     'if_arrow-up.svg'))
        upIcon = QIcon(upPix)
        self.dlg.upBtn.setIcon(upIcon)
        self.dlg.upBtn.setIconSize(0.02*upPix.rect().size())

        downPix = QPixmap(os.path.join(self.plugin_dir,
                                       'if_arrow-down.svg'))
        downIcon = QIcon(downPix)
        self.dlg.downBtn.setIcon(downIcon)
        self.dlg.downBtn.setIconSize(0.02*downPix.rect().size())

        self.dlg.upBtn.clicked.connect(self.ordUp)
        self.dlg.upBtn.setToolTip(u'順序上移')
        self.dlg.downBtn.clicked.connect(self.ordDown)
        self.dlg.downBtn.setToolTip(u'順序下移')

    def run(self):
        result = self.dlg.exec_()
        return result

    def setTable(self):
        table = self.dlg.zoneSeqTable
        table.setRowCount(len(self.zoneOrd))
        table.setColumnCount(2)

        for i in range(0, len(self.zoneOrd)):
            table.setItem(i, 0, QTableWidgetItem(self.zoneOrd[i]))
            table.setItem(i, 1, QTableWidgetItem(str(i+1)))

    def ordUp(self):
        zoneOrd = self.zoneOrd
        table = self.dlg.zoneSeqTable

        c_row = table.currentRow()

        if c_row > 0:
            physName = table.item(c_row, 0).text()
            c_index = zoneOrd.index(physName)

            zoneOrd.pop(c_index)
            zoneOrd.insert(c_index-1, physName)
            self.zoneOrd = zoneOrd
            self.setTable()

        else:
            pass

    def ordDown(self):
        zoneOrd = self.zoneOrd
        table = self.dlg.zoneSeqTable

        c_row = table.currentRow()

        if c_row < table.rowCount()-1:
            physName = table.item(c_row, 0).text()
            c_index = zoneOrd.index(physName)

            zoneOrd.pop(c_index)
            zoneOrd.insert(c_index+1, physName)
            self.zoneOrd = zoneOrd
            self.setTable()

        else:
            pass
