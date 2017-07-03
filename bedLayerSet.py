
import os.path
from PyQt4.QtCore import QSettings, qVersion, QTranslator, QCoreApplication
from PyQt4.QtGui import QTableWidgetItem, QComboBox
from bedLayerDiag import bedLayerDialog


class bedLayer:
    def __init__(self, iface, gradNum, caption, rockUsed=False, rockTypes=0):
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

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.dlg = bedLayerDialog()
        self.dlg.label.setText(caption)

        self.grads = int(gradNum)
        self.rockType = rockTypes
        items1 = ['Fraction', 'Cumulative']
        items2 = ['Fraction', 'Cumulative', 'Rock']

        if rockUsed:
            self.dlg.recTypeCombo.addItems(items2)
        else:
            self.dlg.recTypeCombo.addItems(items1)

        self.setTable()
        self.dlg.recTypeCombo.currentIndexChanged.connect(self.setTable)
        self.dlg.addColumnBtn.pressed.connect(self.addColumn)
        self.dlg.removeColumnBtn.pressed.connect(self.killColumn)

    def run(self):
        result = self.dlg.exec_()

        if result:
            return self.resultString()

    def resultString(self):
        table = self.dlg.layerPropTable
        firstEle = self.dlg.recTypeCombo.currentText()

        columns = table.columnCount()
        physicString = (self.dlg.layerPropTable.item(1, 0).text() + " " +
                        self.dlg.layerPropTable.cellWidget(
                            1, 1).currentText())
        secondEle = ''
        if self.dlg.recTypeCombo.currentIndex() == 0:
            for j in range(0, columns):
                secondEle = secondEle + table.item(3, j).text() + " "
            secondEle = secondEle[:-1]
        elif self.dlg.recTypeCombo.currentIndex() == 1:
            for j in range(0, columns):
                secondEle = secondEle + table.item(3, j).text() + " "
                secondEle = secondEle + table.item(5, j).text() + " "
            secondEle = secondEle[:-1]
        elif self.dlg.recTypeCombo.currentIndex() == 2:
            secondEle = table.cellWidget(2, 1).currentText()

        resultString = firstEle + ' ' + secondEle
        return physicString, resultString

    def addColumn(self):
        table = self.dlg.layerPropTable
        idx = table.columnCount()
        table.insertColumn(idx)
        table.setItem(0, idx, QTableWidgetItem('D'+str(idx+1)))
        table.setItem(2, idx, QTableWidgetItem('P'+str(idx+1)))

    def killColumn(self):
        idx = self.dlg.layerPropTable.columnCount()
        table = self.dlg.layerPropTable
        table.removeColumn(idx-1)

    def setTable(self):
        table = self.dlg.layerPropTable
        table.clear()
        UnitSelector = QComboBox()
        UnitSelector.addItems(['SI', 'EN'])
        if self.dlg.recTypeCombo.currentIndex() == 0:
            self.dlg.addColumnBtn.setEnabled(False)
            self.dlg.removeColumnBtn.setEnabled(False)
            table.setRowCount(4)
            table.setColumnCount(self.grads)

            table.setItem(0, 0, QTableWidgetItem('Thickness'))
            table.setItem(0, 1, QTableWidgetItem('Unit'))
            table.setItem(0, 2, QTableWidgetItem('Density of\nClay'))
            table.setItem(1, 0, QTableWidgetItem(u''))
            table.setCellWidget(1, 1, UnitSelector)
            table.setItem(1, 2, QTableWidgetItem(u''))

            for j in range(0, self.grads):
                table.setItem(2, j, QTableWidgetItem('V'+str(j+1)))
                table.setItem(3, j, QTableWidgetItem(u''))
        elif self.dlg.recTypeCombo.currentIndex() == 1:
            self.dlg.addColumnBtn.setEnabled(True)
            self.dlg.removeColumnBtn.setEnabled(True)
            table.setRowCount(4)
            table.setColumnCount(3)

            table.setItem(0, 0, QTableWidgetItem('Thickness'))
            table.setItem(0, 1, QTableWidgetItem('Unit'))
            table.setItem(0, 2, QTableWidgetItem('Density of\nClay'))
            table.setItem(1, 0, QTableWidgetItem(u''))
            table.setCellWidget(1, 1, UnitSelector)
            table.setItem(1, 2, QTableWidgetItem(u''))

            for j in range(0, table.columnCount()):
                table.setItem(2, j, QTableWidgetItem('D'+str(j+1)))
                table.setItem(3, j, QTableWidgetItem(u''))
                table.setItem(4, j, QTableWidgetItem('P'+str(j+1)))
                table.setItem(5, j, QTableWidgetItem(u''))
        elif self.dlg.recTypeCombo.currentIndex() == 2:
            self.dlg.addColumnBtn.setEnabled(False)
            self.dlg.removeColumnBtn.setEnabled(False)

            table.setColumnCount(2)
            table.setRowCount(3)
            rockTypeBox = QComboBox()
            for j in range(0, self.rockType):
                rockTypeBox.addItem(str(j+1))

            table.setItem(0, 0, QTableWidgetItem('Thickness'))
            table.setItem(0, 1, QTableWidgetItem('Unit'))
            table.setItem(0, 2, QTableWidgetItem('Density of\nClay'))
            table.setItem(1, 0, QTableWidgetItem(u''))
            table.setCellWidget(1, 1, UnitSelector)
            table.setItem(1, 2, QTableWidgetItem(u''))

            table.setItem(2, 0, QTableWidgetItem('Type of Rocks'))
            table.setCellWidget(2, 1, rockTypeBox)
