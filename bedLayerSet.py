
import os.path
from PyQt4.QtCore import QSettings, qVersion, QTranslator, QCoreApplication
from PyQt4.QtGui import QTableWidgetItem, QComboBox
from bedLayerDiag import bedLayerDialog
import subprocess
import copy
import re


class bedLayer:
    def __init__(self, iface, gradNum, caption, rockUsed=False,
                 presetString=''):
        self.iface = iface
        self.preset = presetString

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

        self.grads = len(gradNum)
        self.gradsPartical = gradNum

        items1 = ['Fraction', 'Cumulative']
        items2 = ['Fraction', 'Cumulative', 'Rock']

        if rockUsed:
            self.dlg.recTypeCombo.addItems(items2)
        else:
            self.dlg.recTypeCombo.addItems(items1)

        self.stringParser()
        self.setTable()
        self.setPreset()
        self.dlg.recTypeCombo.currentIndexChanged.connect(self.setTable)
        self.dlg.addColumnBtn.clicked.connect(self.addColumn)
        self.dlg.removeColumnBtn.clicked.connect(self.killColumn)
        self.dlg.chartBtn.clicked.connect(self.drawBedGrad)

    def run(self):
        result = self.dlg.exec_()

        if result:
            return self.resultString()

    def drawBedGrad(self):
        gnuExe = os.path.join(self.plugin_dir, 'gnuplot', 'gnuplot')
        table = self.dlg.layerPropTable
        columns = table.columnCount()
        f = open(os.path.join(self.plugin_dir, 'data.dat'), 'w')
        filename = os.path.join(self.plugin_dir, 'data.dat')

        if self.dlg.recTypeCombo.currentIndex() == 0:
            particals = self.gradsPartical
            fraction = list()

            grad = list()
            grad.append(particals[0][0])
            for i in range(0, len(particals)):
                grad.append(particals[i][1])

            fraction.append(0.0)
            for j in range(0, columns):
                fraction.append(float(table.item(3, j).text()))
            cum_fraction = copy.copy(fraction)
            for i in range(1, len(cum_fraction)):
                cum_fraction[i] = sum(fraction[0:i+1])

            for i in range(0, len(grad)):
                f.write(str(grad[i]) + ' ' + str(cum_fraction[i]) + '\n')
            f.close()

            f = open(os.path.join(self.plugin_dir, 'plot.dem'), 'w')
            f.write('set ylabel "%"\n')
            f.write('set xlabel "D (mm)"\n')
            f.write('set logscale x\n')
            f.write('set style line 1 lt 2 lw 1.5 lc rgb "blue"\n')
            f.write('set key off\n')
            f.write('plot "' + filename.replace('\\', '/') +
                    '" with lines ls 1')
            f.close()

            subprocess.Popen([gnuExe,
                              os.path.join(self.plugin_dir, 'plot.dem'),
                              '--persist'], shell=False)

        elif self.dlg.recTypeCombo.currentIndex() == 1:
            D = list()
            P = list()
            D.append(str(self.gradsPartical[0][0]))
            P.append(str(0))
            for j in range(0, columns):
                D.append(float(table.item(3, j).text()))
                P.append(float(table.item(5, j).text()))

            for i in range(0, len(D)):
                f.write(str(D[i]) + ' ' + str(P[i]) + '\n')
            f.close()

            f = open(os.path.join(self.plugin_dir, 'plot.dem'), 'w')
            f.write('set ylabel "%"\n')
            f.write('set xlabel "D (mm)"\n')
            f.write('set logscale x\n')
            f.write('set style line 1 lt 2 lw 1.5 lc rgb "red"\n')
            f.write('set key off\n')
            f.write('plot "' + filename.replace('\\', '/') +
                    '" with lines ls 1\n')
            f.close()

            subprocess.Popen([gnuExe,
                              os.path.join(self.plugin_dir, 'plot.dem'),
                              '--persist'], shell=False)

    def stringParser(self):
        if self.preset:
            string = re.split(';', self.preset)

            line1 = string[1].split()
            method = line1[0].upper()
            if method == 'FRACTION':
                self.dlg.recTypeCombo.setCurrentIndex(0)
            elif method == 'CUMULATIVE':
                self.dlg.recTypeCombo.setCurrentIndex(1)
            else:
                self.dlg.recTypeCombo.setCurrentIndex(2)

    def setPreset(self):
        if self.preset:
            try:
                string = re.split(';', self.preset)
                line0 = string[0].split()
                depth = line0[0]
                unit = line0[1].upper()
                self.dlg.layerPropTable.item(1, 0).setText(depth)
                if unit == 'SI':
                    self.dlg.layerPropTable.cellWidget(1, 1).setCurrentIndex(0)
                else:
                    self.dlg.layerPropTable.cellWidget(1, 1).setCurrentIndex(1)

                line1 = string[1].split()
                method = line1[0].upper()
                if method == 'FRACTION':
                    self.dlg.recTypeCombo.setCurrentIndex(0)
                    for i in range(1, len(line1)):
                        j = i-1
                        self.dlg.layerPropTable.item(3, j).setText(line1[i])
                elif method == 'CUMULATIVE':
                    self.dlg.recTypeCombo.setCurrentIndex(1)
                    n = len(line1)
                    if n-1 > 14:
                        while 2*self.dlg.layerPropTable.columnCount() < n-1:
                            self.addColumn()
                    j = 0
                    for i in range(1, len(line1), 2):
                        self.dlg.layerPropTable.item(3, j).setText(line1[i])
                        j += 1
                    t = 0
                    for k in range(2, len(line1), 2):
                        self.dlg.layerPropTable.item(5, t).setText(line1[k])
                        t += 1
                else:
                    self.dlg.layerPropTable.cellWidget(2, 1).setCurrentIndex(
                        int(line1[1])-1)
            except:
                pass

    def resultString(self):
        table = self.dlg.layerPropTable
        firstEle = self.dlg.recTypeCombo.currentText().upper()

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
            secondEle = ''

        resultString = firstEle + ' ' + secondEle
        return physicString, resultString

    def addColumn(self):
        table = self.dlg.layerPropTable
        idx = table.columnCount()
        table.insertColumn(idx)
        table.setItem(2, idx, QTableWidgetItem('D'+str(idx+1)))
        table.setItem(4, idx, QTableWidgetItem('P'+str(idx+1)))
        table.setItem(3, idx, QTableWidgetItem(''))
        table.setItem(5, idx, QTableWidgetItem(''))

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
            table.setItem(0, 2, QTableWidgetItem(
                'Density of\n Clay\n(optional)'))
            table.setItem(1, 0, QTableWidgetItem(u''))
            table.setCellWidget(1, 1, UnitSelector)
            table.setItem(1, 2, QTableWidgetItem(u''))

            for j in range(0, self.grads):
                table.setItem(2, j, QTableWidgetItem('V'+str(j+1)))
                table.setItem(3, j, QTableWidgetItem(u''))
            self.dlg.chartBtn.setEnabled(True)
        elif self.dlg.recTypeCombo.currentIndex() == 1:
            self.dlg.addColumnBtn.setEnabled(True)
            self.dlg.removeColumnBtn.setEnabled(True)
            table.setRowCount(6)
            table.setColumnCount(7)

            table.setItem(0, 0, QTableWidgetItem('Thickness'))
            table.setItem(0, 1, QTableWidgetItem('Unit'))
            table.setItem(0, 2, QTableWidgetItem(
                'Density of\n Clay\n(optional)'))
            table.setItem(1, 0, QTableWidgetItem(u''))
            table.setCellWidget(1, 1, UnitSelector)
            table.setItem(1, 2, QTableWidgetItem(u''))

            for j in range(0, table.columnCount()):
                table.setItem(2, j, QTableWidgetItem('D'+str(j+1)))
                table.setItem(3, j, QTableWidgetItem(u''))
                table.setItem(4, j, QTableWidgetItem('P'+str(j+1)))
                table.setItem(5, j, QTableWidgetItem(u''))
            self.dlg.chartBtn.setEnabled(True)
        elif self.dlg.recTypeCombo.currentIndex() == 2:
            self.dlg.addColumnBtn.setEnabled(False)
            self.dlg.removeColumnBtn.setEnabled(False)

            table.setColumnCount(2)
            table.setRowCount(2)

            table.setItem(0, 0, QTableWidgetItem('Thickness'))
            table.setItem(0, 1, QTableWidgetItem('Unit'))
            table.setItem(0, 2, QTableWidgetItem(
                'Density of\n Clay\n(optional)'))
            table.setItem(1, 0, QTableWidgetItem(u''))
            table.setCellWidget(1, 1, UnitSelector)
            table.setItem(1, 2, QTableWidgetItem(u''))

            self.dlg.chartBtn.setEnabled(False)
