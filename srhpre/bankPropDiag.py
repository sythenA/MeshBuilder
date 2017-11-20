
import os
import os.path
from PyQt4 import uic
from PyQt4.QtGui import QDialog, QTableWidgetItem


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'bankPropDiag.ui'))


class bankPropDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(bankPropDialog, self).__init__(parent)
        self.setupUi(self)


class bankProp:
    def __init__(self, iface, parentDiag):
        self.iface = iface
        self.dlg = bankPropDialog()

        self.setToLVRatio()
        self.dlg.modelCombo.currentIndexChanged.connect(self.switchTable)
        if parentDiag.bankModBox.currentIndex() == 3:
            self.dlg.modelCombo.setEnabled(False)
            self.setToLinearRet()
        elif parentDiag.bankModBox.currentIndex() == 4:
            self.dlg.modelCombo.setEnabled(False)
            self.setToAoR()
        self.parentDiag = parentDiag

    def switchTable(self):
        if self.dlg.modelCombo.currentIndex() == 0:
            self.setToLVRatio()
        elif self.dlg.modelCombo.currentIndex() == 1:
            self.setToErodibility()
        else:
            self.setToCriticalStress()

    def resultString(self):
        idx = self.dlg.modelCombo.currentIndex()
        table = self.dlg.parameterTable
        propString = ''
        if self.parentDiag.bankModBox.currentIndex() == 0:
            if idx == 0:
                propString = table.item(0, 0).text()
            else:
                for i in range(0, table.columnCount()):
                    propString += (table.item(0, i).text() + ' ')
                propString = propString[:-1]

            finalString = str(idx+1) + ';' + propString
        elif (self.parentDiag.bankModBox.currentIndex() == 3 or
                self.parentDiag.bankModBox.currentIndex() == 4):
            for i in range(0, table.columnCount()):
                propString += (table.item(0, i).text() + ' ')
            propString = propString[:-1]
            finalString = propString

        return finalString

    def setToLinearRet(self):
        table = self.dlg.parameterTable
        table.setColumnCount(3)
        table.setRowCount(1)
        table.setHorizontalHeaderLabels([u'Erodibility (m/s)',
                                         u'Tau_Cri_L (Pa)', 'AoR*'])
        self.dlg.label_3.setText('*Angle of Respondse')

        table.setColumnWidth(0, 112)
        table.setColumnWidth(1, 112)
        table.setColumnWidth(2, 112)
        table.setColumnWidth(3, 112)

    def setToLVRatio(self):
        table = self.dlg.parameterTable
        table.setColumnCount(1)
        table.setRowCount(1)
        table.setHorizontalHeaderLabels([u'L to V Ratio'])
        table.setItem(0, 0, QTableWidgetItem(u''))

        table.setColumnWidth(0, 150)

    def setToErodibility(self):
        table = self.dlg.parameterTable
        table.setColumnCount(3)
        table.setRowCount(1)

        table.setHorizontalHeaderLabels([u'Erodibility (m/s)',
                                         u'Tau_Cri_L (Pa)', u'Exp'])
        table.setItem(0, 0, QTableWidgetItem(u''))
        table.setItem(0, 1, QTableWidgetItem(u''))
        table.setItem(0, 2, QTableWidgetItem(u''))

        table.setColumnWidth(0, 150)
        table.setColumnWidth(1, 150)
        table.setColumnWidth(2, 150)

    def setToCriticalStress(self):
        table = self.dlg.parameterTable
        table.setColumnCount(2)
        table.setRowCount(1)

        table.setHorizontalHeaderLabels([u'Tau_Cri_L (Pa)', u'Tau_Cri_V (Pa)'])
        table.setItem(0, 0, QTableWidgetItem(u''))
        table.setItem(0, 1, QTableWidgetItem(u''))

        table.setColumnWidth(0, 150)
        table.setColumnWidth(1, 150)

    def setToAoR(self):
        table = self.dlg.parameterTable
        table.setColumnCount(2)
        table.setRowCount(1)

        table.setHorizontalHeaderLabels([u'Dry AoR', u'Wet AoR'])
        table.setItem(0, 0, QTableWidgetItem(u''))
        table.setItem(0, 1, QTableWidgetItem(u''))
        table.setColumnWidth(0, 150)
        table.setColumnWidth(1, 150)

        self.dlg.label_2.setText(u'Set Angle of Respondse(AoR)')

    def run(self):
        result = self.dlg.exec_()
        if result:
            propString = self.resultString()
            return propString
