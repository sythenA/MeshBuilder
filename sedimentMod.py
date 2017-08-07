# -*- coding: big5 -*-

from PyQt4.QtGui import QComboBox, QTableWidgetItem, QTreeWidgetItem, QCheckBox
from PyQt4.QtCore import Qt
from qgis.utils import iface
from commonDialog import fileBrowser, onCritical
from bedLayerSet import bedLayer
from quasiSediOption import quasiSedimentSetting
from selectMeshDiag import meshSelector
from math import ceil
from bankPropDiag import bankProp
import re
import shepred
import os.path


class sedimentModule:
    def __init__(self, dlg):
        self.dlg = dlg
        self.dlg.sediSizeClass.textChanged.connect(self.setGradTable)
        self.dlg.sedimentTab.setCurrentIndex(0)

        self.dlg.capacityEqnCombo.currentIndexChanged.connect(
            self.setCapEqnTable)

        self.dlg.checkCohesiveUsed.stateChanged.connect(self.useCohesive)
        self.dlg.cohFallVelCombo.currentIndexChanged.connect(
            self.checkCohFallVel)
        self.dlg.sameFileAsFlowBox.stateChanged.connect(self.useTwo2dmFile)
        self.bedSet = bedSettingModule(self.dlg)
        self.quasiSedi = False
        self.dlg.sediModelingCombo.currentIndexChanged.connect(
            self.sedimentModelingSetting)
        self.dlg.sediStartingEdit.setText(self.dlg.lineEditTStart.text())

    def useTwo2dmFile(self):
        if self.dlg.sameFileAsFlowBox.checkState() == Qt.Unchecked:
            self.dlg.setBed2dmBtn.setEnabled(True)
        else:
            self.dlg.setBed2dmBtn.setEnabled(False)

    def sedimentModelingSetting(self):
        try:
            quasi_interval = self.quasi_interval
        except:
            quasi_interval = ''
        try:
            quasi_dt = self.quasi_dt
        except:
            quasi_dt = ''

        if self.dlg.sediModelingCombo.currentIndex() == 0:
            self.quasiSedi = False
        else:
            self.quasiSedi = True
            qDlg = quasiSedimentSetting(iface, quasi_interval, quasi_dt)
            quasi_interval, quasi_dt = qDlg.run()
            if quasi_interval:
                self.quasi_interval = quasi_interval
            if quasi_dt:
                self.quasi_dt = quasi_dt
            try:
                if self.quasi_interval and self.quasi_dt:
                    self.dlg.label_41.setText('Quasi-Steady set done.')
            except:
                pass

    def checkCohFallVel(self):
        idx = self.dlg.cohFallVelCombo.currentIndex()
        if idx == 2:
            self.dlg.label_40.setText(
                'Please assign a file containing cohesive sediment \n\
concentration and falling velocity relation.')
            caption = u'請選擇指定顆粒落下速度與粒徑關係的檔案'
            fileBrowser(self.dlg, caption, self.dlg.projFolder,
                        self.dlg.label_40, '*.*')

    def cleanEqDependentTable(self):
        self.dlg.eqDependentTable.clear()
        self.dlg.eqDependentTable.setRowCount(0)
        self.dlg.eqDependentTable.setColumnCount(0)

    def setClimit(self):
        if self.dlg.sediPropTable.item(0, 1).text():
            self.dlg.cohDiaLimEdit.setText(
                self.dlg.sediPropTable.item(0, 1).text())

    def setGradTable(self):
        try:
            gradLvl = int(self.dlg.sediSizeClass.text())
            self.dlg.sediPropTable.setRowCount(gradLvl)
            self.dlg.sediPropTable.setColumnCount(4)
            header = ['D_min (mm)', 'D_max (mm)', 'Dry Bulk\nDensity',
                      'Unit']
            self.dlg.sediPropTable.setHorizontalHeaderLabels(header)
            unitCombo = QComboBox()
            unitCombo.addItem('SI')
            unitCombo.addItem('EN')

            for i in range(0, gradLvl):
                unitCombo = QComboBox()
                unitCombo.addItem('SI')
                unitCombo.addItem('EN')
                self.dlg.sediPropTable.setCellWidget(i, 3, unitCombo)
                for j in range(0, 3):
                    self.dlg.sediPropTable.setItem(i, j, QTableWidgetItem(u''))
            self.dlg.sediPropTable.itemChanged.connect(self.setClimit)

        except(ValueError):
            self.dlg.sediPropTable.clear()

    def setCapEqnTable(self):
        self.dlg.eqDependentTable.clear()
        self.dlg.eqDependentTable.setRowCount(0)
        self.dlg.eqDependentTable.setColumnCount(0)

        idx = self.dlg.capacityEqnCombo.currentIndex()
        if idx == 3 or idx == 11:
            self.dlg.eqDependentTable.setRowCount(1)
            self.dlg.eqDependentTable.setColumnCount(3)
            header = ['T1', 'T2', 'D_SAND (mm)']
            self.dlg.eqDependentTable.setHorizontalHeaderLabels(header)

            for i in range(0, self.dlg.eqDependentTable.rowCount()):
                for j in range(0, self.dlg.eqDependentTable.columnCount()):
                    self.dlg.eqDependentTable.setItem(
                        i, j, QTableWidgetItem(u''))

            if idx == 3:
                self.dlg.eqDependentTable.setItem(0, 0,
                                                  QTableWidgetItem(u'0.021'))
                self.dlg.eqDependentTable.setItem(0, 1,
                                                  QTableWidgetItem(u'0.038'))
                self.dlg.eqDependentTable.setItem(0, 2,
                                                  QTableWidgetItem(u'1.0'))
            else:
                self.dlg.eqDependentTable.setItem(0, 0,
                                                  QTableWidgetItem(u'0.021'))
                self.dlg.eqDependentTable.setItem(0, 1,
                                                  QTableWidgetItem(u'0.0365'))
                self.dlg.eqDependentTable.setItem(0, 2,
                                                  QTableWidgetItem(u'2.0'))
        elif idx in [1, 7, 8]:
            self.dlg.eqDependentTable.setRowCount(1)
            self.dlg.eqDependentTable.setColumnCount(1)
            header = ['HF']
            self.dlg.eqDependentTable.setHorizontalHeaderLabels(header)

            for i in range(0, self.dlg.eqDependentTable.rowCount()):
                for j in range(0, self.dlg.eqDependentTable.columnCount()):
                    self.dlg.eqDependentTable.setItem(i, j,
                                                      QTableWidgetItem(u''))
            self.dlg.eqDependentTable.setItem(0, 0, QTableWidgetItem(u'0.0'))

        elif idx == 2 or idx == 9:
            self.dlg.eqDependentTable.setRowCount(1)
            self.dlg.eqDependentTable.setColumnCount(2)
            header = ['THETA', 'HF']
            self.dlg.eqDependentTable.setHorizontalHeaderLabels(header)

            for i in range(0, self.dlg.eqDependentTable.rowCount()):
                for j in range(0, self.dlg.eqDependentTable.columnCount()):
                    self.dlg.eqDependentTable.setItem(i, j,
                                                      QTableWidgetItem(u''))

            self.dlg.eqDependentTable.setItem(0, 0, QTableWidgetItem(u'0.04'))
            self.dlg.eqDependentTable.setItem(0, 1, QTableWidgetItem(u'0.65'))

        elif idx == 4:
            self.dlg.eqDependentTable.setRowCount(1)
            self.dlg.eqDependentTable.setColumnCount(1)
            header = ['THETA_CRI']
            self.dlg.eqDependentTable.setHorizontalHeaderLabels(header)

            for i in range(0, self.dlg.eqDependentTable.rowCount()):
                for j in range(0, self.dlg.eqDependentTable.columnCount()):
                    self.dlg.eqDependentTable.setItem(i, j,
                                                      QTableWidgetItem(u''))
            self.dlg.eqDependentTable.setItem(0, 0, QTableWidgetItem(u'0.03'))

    def useCohesive(self):
        if self.dlg.checkCohesiveUsed.checkState() == Qt.Checked:
            self.dlg.cohDiaLimEdit.setEnabled(True)
            self.dlg.cohFallVelCombo.setEnabled(True)
            self.dlg.cohSediEroRateGroup.setEnabled(True)
            self.dlg.cohSediDepRateGroup.setEnabled(True)

            self.dlg.tauEsEdit.setEnabled(True)
            self.dlg.tauEmEdit.setEnabled(True)
            self.dlg.ssEdit.setEnabled(True)
            self.dlg.smEdit.setEnabled(True)
            self.dlg.tauDfEdit.setEnabled(True)
            self.dlg.tauDpEdit.setEnabled(True)
            self.dlg.concEqEdit.setEnabled(True)
            self.dlg.unitBox_1.setEnabled(True)
            self.dlg.unitBox_2.setEnabled(True)
        else:
            self.dlg.cohDiaLimEdit.setEnabled(False)
            self.dlg.cohFallVelCombo.setEnabled(False)
            self.dlg.cohSediEroRateGroup.setEnabled(False)
            self.dlg.cohSediDepRateGroup.setEnabled(False)

    def sediSteadyExport(self):
        line = '// Quasi Unsteady Modeling for Sediment? [time_interval(hrs) \
dt_sed(s)] [Empty=Full-Uns]\n'
        if self.quasiSedi:
            line += (str(self.quasi_interval) + ' ')
            line += (str(self.quasi_dt))
            line += '\n'
        else:
            line += '\n'
        self.quasiString = line

    def sediGradExport(self):
        gradString = '// General Sediment Parameters: spec_grav sed_nclass\n'
        gradString = (gradString + self.dlg.sediSGEdit.text() + " " +
                      self.dlg.sediSizeClass.text() + '\n')
        table = self.dlg.sediPropTable

        gradString = gradString + '// Property-of-Size-Class: D_Lower(mm) \
D_Upper(mm) [Den_Bulk] [SI/EN]\n'
        line = ''
        for i in range(0, table.rowCount()):
            line = line + (table.item(i, 0).text() + " " +
                           table.item(i, 1).text() + ' ')
            if table.item(i, 2).text():
                line = line + table.item(i, 2).text() + " "
                line = line + table.cellWidget(i, 3).currentText() + '\n'
            else:
                line = line + '\n'
        line += '// Are You Specifying Fall-Velocity, Transport-Capacity and \
Mode for each Size Class? (YES or NO)\n'
        line += 'NO\n'
        self.sediGradText = gradString + line

    def sediCapacity(self):
        idx = self.dlg.capacityEqnCombo.currentIndex()
        table = self.dlg.eqDependentTable
        capacityString = '// Sediment Transport Capacity Equation (EH MPM PARK \
WILC WU YANG73 YANG79 TRI BAG KUO AW RIJN USER GAR WRI MIX\n'
        if idx == 0:
            capacityString += 'EH\n'
        elif idx == 1:
            capacityString += 'MPM\n'
            capacityString += '// Capacity Equation Hiding Factor (0 to 0.9)\n'
            capacityString = capacityString + table.item(0, 0).text() + '\n'
        elif idx == 2:
            capacityString += 'PARKER\n'
            capacityString += '// Capacity Equation Coefficients for Parker \
and/or Seminara (Theta_Critial Hiding Factor)\n'
            capacityString = (capacityString + table.item(0, 0).text() + ' ' +
                              table.item(0, 1).text() + '\n')
        elif idx == 6:
            capacityString += 'YANG79\n'
        elif idx == 5:
            capacityString += 'YANG73\n'
        elif idx == 3:
            capacityString += 'WILCOCK\n'
            capacityString += '// Wicock Capacity Equation Coefficients: T1 T2 \
d_sand; Theta=T1+(T2-T1)*Exp(-20F_s)\n'
            capacityString += (table.item(0, 0).text() + ' ')
            capacityString += (table.item(0, 1).text() + ' ')
            capacityString += (table.item(0, 2).text() + '\n')
        elif idx == 4:
            capacityString += 'WU\n'
            capacityString += '// Wu Capacity Equation Critical Shields Number\
(0.01 to 0.07)\n'
            capacityString += (table.item(0, 0).text() + '\n')
        elif idx == 7:
            capacityString += 'AW\n'
            capacityString += '// Capacity Equation Hiding Factor (0 to 0.9)\n'
            capacityString += (table.item(0, 0).text() + '\n')
        elif idx == 8:
            capacityString += 'RIJN\n'
            capacityString += '// Capacity Equation Hiding Factor (0 to 0.9)\n'
            capacityString += (table.item(0, 0).text() + '\n')
        elif idx == 9:
            capacityString += 'SEMI\n'
            capacityString += '// Capacity Equation Hiding Factor (0 to 0.9)\n'
            capacityString += '// Capacity Equation Coefficients for Parker \
and/or Seminara (Theta_Critial Hiding Factor)\n'
            capacityString += (table.item(0, 0).text() + ' ' +
                               table.item(0, 1).text() + '\n')
        elif idx == 10:
            capacityString += 'BAGNOLD\n'
        elif idx == 11:
            capacityString += 'TRINITY\n'
            capacityString += '//Trinity Capacity Equation Coefficients: T1 T2 \
d_sand; Theta=T1+(T2-T1)*Exp(-20F_s)\n'
            capacityString += (table.item(0, 0).text() + ' ')
            capacityString += (table.item(0, 1).text() + ' ')
            capacityString += (table.item(0, 2).text() + '\n')
        elif idx == 12:
            capacityString += 'KUO\n'

        capacityString += '// Water Temperature (Celsius):\n'
        if self.dlg.watTempEdit.text():
            capacityString += (self.dlg.watTempEdit.text() + '\n')
        else:
            capacityString += ('25.0' + '\n')
        capacityString += '// Start Time in hours for the Sediment Solver\n'
        if self.dlg.sediStartingEdit.text():
            capacityString += str(int(self.dlg.sediStartingEdit.text()))
            capacityString += '\n'
        else:
            capacityString += '\n'
        capacityString = capacityString + '// Adaptation Coefs for Suspended\
 Load: A_DEP A_ERO (0.25 1.0 are defaults)\n'
        capacityString += (self.dlg.suspCoefEdit.text() + ' ')
        capacityString += (self.dlg.bedLoadCoefEdit.text() + '\n')

        capacityString = capacityString + '// Bedload Adaptation Length: \
MOD_ADAP_LNG LENGTH(meter) (0=const;1=Sutherland; 2/3=van Rijn; 4=Seminara)\n'
        capacityString += (str(self.dlg.adaptionLenCombo.currentIndex()) + ' ' +
                           self.dlg.bLoadAdaptionLenEdit.text() + '\n')

        capacityString += '// Active Layer Thickness: \
MOD_ALayer NALT (1=const;2=Nalt*d90)\n'
        capacityString = (capacityString +
                          str(self.dlg.aTMode.currentIndex() + 1) + ' ')
        if self.dlg.tParaEdit.text():
            capacityString += self.dlg.tParaEdit.text() + '\n'
        else:
            capacityString += '10' + '\n'
        self.capacityText = capacityString

    def cohExportText(self, cohText):
        cohText += '// Cohesive Sediment General Properties (C_limit(mm),\
MOD_consolidation)\n'
        cohText += self.dlg.cohDiaLimEdit.text() + '\n'
        cohText += '// Cohesive Sediment Fall Velocity Method: 0 -1 or\
 filename\n'
        if self.dlg.cohFallVelCombo.currentIndex() == 0:
            cohText += '-1\n'
        elif self.dlg.cohFallVelCombo.currentIndex() == 1:
            cohText += '0\n'
        else:
            cohText += (self.dlg.label_40.text() + '\n')
        cohText += '// Cohesive Sediment Erosion Rate: 0=4-parameter-method or \
a filename\n'
        cohText += '0\n'  # Currently only Four-Parameter Method provided.
        cohText += '// Cohesive Sediment Constants (Pa mm/s): ss_es ss_em \
slope_s slope_m\n'
        cohText += (self.dlg.tauEsEdit.text() + ' ' + self.dlg.tauEmEdit.text())
        cohText += ' '
        cohText += (self.dlg.ssEdit.text() + ' ' + self.dlg.smEdit.text() + ' ')
        cohText = cohText + self.dlg.unitBox_1.currentText() + '\n'

        cohText += '// Cohesive Deposition Parameters (N/m2 kg/m3): ss_df ss_dp\
 conc_eq\n'
        cohText += (self.dlg.tauDfEdit.text() + ' ' + self.dlg.tauDpEdit.text())
        cohText += (' ' + self.dlg.concEqEdit.text() + ' ')
        cohText += (self.dlg.unitBox_1.currentText() + '\n')

        return cohText

    def cohesiveExport(self):
        cohText = '// MOD_COHESIVE (0=non-cohesive 1=cohesive)\n'
        if self.dlg.checkCohesiveUsed.isChecked():
            cohText = cohText + '1\n'
            cohText = self.cohExportText(cohText)
        else:
            cohText = cohText + '0\n'

        self.cohText = cohText

    def sediExport(self):
        self.sediSteadyExport()
        self.sediGradExport()
        self.sediCapacity()
        self.cohesiveExport()

        self.bedSet.bedLayersExport()
        self.bedLayerText = self.bedSet.layerText


class bedSettingModule:
    def __init__(self, dlg):
        self.dlg = dlg
        self.dlg.bedLayerTree.clear()
        self.getPhysRegionFromMain()
        self.setBedToUniform()
        self.dlg.rdoBedUniform.toggled.connect(self.setBedToUniform)
        self.dlg.rdoBedZonal.toggled.connect(self.setBedToZone)
        self.dlg.rockErosionCheck.stateChanged.connect(self.rockAllowed)
        self.dlg.readMeshBtn.pressed.connect(self.getPhysRegionFromMain)
        self.dlg.setBed2dmBtn.clicked.connect(self.getBedPhysRegion)

    def rockAllowed(self):
        if self.dlg.rockErosionCheck.checkState() == Qt.Checked:
            self.dlg.typesOfRockEdit.setEnabled(True)
            self.dlg.bedRockSetTable.setEnabled(True)
            self.dlg.typesOfRockEdit.textChanged.connect(self.setRockProperties)
        else:
            self.dlg.typesOfRockEdit.setEnabled(False)

    def setRockProperties(self):
        self.dlg.bedRockSetTable.clear()
        self.dlg.bedRockSetTable.setRowCount(0)
        self.dlg.bedRockSetTable.setColumnCount(0)

        rockTypes = int(self.dlg.typesOfRockEdit.text())
        table = self.dlg.bedRockSetTable
        table.setRowCount(2*rockTypes)
        table.setColumnCount(7)

        for i in range(0, rockTypes):
            proSelector = QComboBox()
            proSelector.addItem('Reclamation')
            proSelector.addItem('Stream-Power')

            proSelector.currentIndexChanged.connect(
                self.setRockPropertyType)
            table.setCellWidget(i*2, 0, proSelector)
            for j in range(1, 6):
                table.setItem(i*2+1, j, QTableWidgetItem(u''))

            self.dlg.bedRockSetTable.setItem(
                i*2, 1, QTableWidgetItem('d_cover'))
            self.dlg.bedRockSetTable.setItem(
                i*2, 2, QTableWidgetItem('K_h'))
            self.dlg.bedRockSetTable.setItem(
                i*2, 3, QTableWidgetItem('TAU_cri'))
            self.dlg.bedRockSetTable.setItem(
                i*2, 4, QTableWidgetItem('K_a'))
            self.dlg.bedRockSetTable.setItem(
                i*2, 5, QTableWidgetItem('Young'))
            self.dlg.bedRockSetTable.setItem(
                i*2, 6, QTableWidgetItem('Tensile'))

    def setRockPropertyType(self):
        c_Row = self.dlg.bedRockSetTable.currentRow()
        box = self.dlg.bedRockSetTable.cellWidget(c_Row, 0)
        if box.currentIndex() == 0:
            self.dlg.bedRockSetTable.setItem(
                c_Row, 1, QTableWidgetItem('d_cover'))
            self.dlg.bedRockSetTable.setItem(
                c_Row, 2, QTableWidgetItem('K_h'))
            self.dlg.bedRockSetTable.setItem(
                c_Row, 3, QTableWidgetItem('TAU_cri'))
            self.dlg.bedRockSetTable.setItem(
                c_Row, 4, QTableWidgetItem('K_a'))
            self.dlg.bedRockSetTable.setItem(
                c_Row, 5, QTableWidgetItem('Young'))
            self.dlg.bedRockSetTable.setItem(
                c_Row, 6, QTableWidgetItem('Tensile'))
            if self.dlg.bedRockSetTable.cellWidget(c_Row+1, 5):
                self.dlg.bedRockSetTable.removeCellWidget(c_Row+1, 5)
                self.dlg.bedRockSetTable.setItem(
                    c_Row+1, 5, QTableWidgetItem(u''))
        elif box.currentIndex() == 1:
            self.dlg.bedRockSetTable.setItem(
                c_Row, 1, QTableWidgetItem('d_cover'))
            self.dlg.bedRockSetTable.setItem(
                c_Row, 2, QTableWidgetItem('E_h'))
            self.dlg.bedRockSetTable.setItem(
                c_Row, 3, QTableWidgetItem('Alpha'))
            self.dlg.bedRockSetTable.setItem(
                c_Row, 4, QTableWidgetItem('Beta'))
            self.dlg.bedRockSetTable.setItem(
                c_Row, 5, QTableWidgetItem('kh'))
            KhSelector = QComboBox()
            KhSelector.setEditable(True)
            KhSelector.addItem(u'')
            KhSelector.addItem('Use File')
            KhSelector.currentIndexChanged.connect(self.useKhFile)
            self.dlg.bedRockSetTable.setCellWidget(c_Row+1, 5, KhSelector)

    def useKhFile(self):
        caption = 'Please choose a file for distributed Kh Value.'
        fileBrowser(self.dlg, caption, self.dlg.projFolder,
                    presetType='*.2dm')

    def getPhysRegionFromMain(self):
        if self.dlg.lineMeshFilePath.text():
            mainMshFilePath = self.dlg.lineMeshFilePath.text()
            boundsRef, physRef = shepred.readMshMesh(mainMshFilePath)
        elif (self.dlg.lineEditMeshFileName.text() and
                not self.dlg.lineMeshFilePath.text()):
            main2dmPath = self.dlg.lineEditMeshFileName.text()
            f = open(main2dmPath, 'r')
            data = f.readlines()
            f.close()
            _physRef, boundsRef = shepred.read2dmMesh(data)
            physRef = dict()
            for i in range(0, len(_physRef)):
                physRef.update({i+1: str(_physRef[i])})
        else:
            boundsRef = list()
            physRef = list()

        self.boundsRef = boundsRef
        self.physRef = physRef

    def getBedPhysRegion(self):
        selector = meshSelector(iface, self.dlg.saveFolderEdit.text())
        result = selector.run()
        if result:
            f = open(selector.mesh2dm)
            meshLines = f.readlines()
            physRef, boundsRef = shepred.read2dmMesh(meshLines)
            physRef.sort()
            _physRef = dict()
            for i in range(0, len(physRef)):
                _physRef.update({i+1: str(physRef[i])})
            self.boundsRef = boundsRef
            self.physRef = _physRef
            self.dlg.label_45.setText(selector.mesh2dm)

            if selector.meshMsh:
                boundsRef, physRef = shepred.readMshMesh(selector.meshMsh)
                self.boundsRef = boundsRef
                self.physRef = physRef

    def setBedToUniform(self):
        try:
            self.dlg.bedLayerTree.itemClicked.disconnect()
        except:
            pass
        self.dlg.bedLayerTree.clear()
        self.dlg.bedLayerTree.setColumnCount(2)
        self.dlg.bedLayerTree.setHeaderLabels(['Layers', 'Status'])
        DomainItem = QTreeWidgetItem()
        DomainItem.setText(0, 'Domain')
        self.dlg.bedLayerTree.addTopLevelItem(DomainItem)
        self.dlg.bedLayerTree.setColumnWidth(0, 150)

        try:
            layerNum = int(self.dlg.layerInZoneEdit.text())
        except:
            layerNum = None
        if layerNum:
            for i in range(0, layerNum):
                layerItem = QTreeWidgetItem(DomainItem)
                layerItem.setText(0, 'Layer '+str(i+1))
        self.dlg.bedLayerTree.itemClicked.connect(self.bedLayerPopUp)

    def setBedToZone(self):
        try:
            self.dlg.bedLayerTree.itemClicked.disconnect()
            self.dlg.zoneBedSelector.clear()
        except:
            pass
        try:
            physRef = self.physRef
        except:
            physRef = None

        if physRef:
            self.dlg.bedLayerTree.clear()
            self.dlg.bedLayerTree.setColumnCount(2)
            self.dlg.bedLayerTree.setHeaderLabels(['Layers', 'Status'])
            for i in range(0, len(physRef)):
                item = QTreeWidgetItem()
                item.setText(0, str(i+1) + ". " + physRef[i+1])
                self.dlg.bedLayerTree.addTopLevelItem(item)
                self.dlg.zoneBedSelector.addItem(str(i+1))
            self.dlg.bedLayerTree.setColumnWidth(0, 150)
            self.dlg.layerInZoneEdit.textChanged.connect(self.setBedLayerInZone)
            self.dlg.bedLayerTree.itemClicked.connect(self.bedLayerPopUp)
        else:
            onCritical(107)

    def setBedToDistri(self):
        try:
            self.dlg.bedLayerTree.itemClicked.disconnect()
            self.dlg.zoneBedSelector.clear()
        except:
            pass
        item = QTreeWidgetItem()
        item.setText(0, 'File Input')
        self.dlg.bedLayerTree.addTopLevelItem(item)
        self.dlg.bedLayerTree.itemClicked.connect(self.inputSelector)

    def inputSelector(self):
        caption = 'Please choose a file for distributed bed layer input.'
        fileBrowser(self.dlg, caption, self.dlg.projFolder,
                    self.dlg.bedDistriEdit, presetType='*.*')

    def setBedLayerInZone(self):
        idx = self.dlg.zoneBedSelector.currentIndex()
        totalLayers = int(self.dlg.layerInZoneEdit.text())
        currentRegion = self.dlg.bedLayerTree.topLevelItem(idx)
        currLayers = currentRegion.childCount()

        if currLayers == 0:
            for i in range(0, totalLayers):
                item = QTreeWidgetItem()
                item.setText(0, 'Layer'+str(i+1))
                currentRegion.addChild(item)
        elif currLayers < totalLayers:
            for i in range(currLayers, totalLayers):
                item = QTreeWidgetItem()
                item.setText(0, 'Layer'+str(i+1))
                currentRegion.addChild(item)
        elif currLayers > totalLayers:
            itemList = list()
            for j in range(totalLayers, currLayers):
                itemList.append(currentRegion.child(j))
            for k in range(0, len(itemList)):
                currentRegion.removeChild(itemList[k])
        else:
            pass

    def bedLayerPopUp(self):
        item = self.dlg.bedLayerTree.currentItem()
        zoneItem = item.parent()
        try:
            presetString = self.nextLayerpreSet
        except:
            presetString = ''
        if zoneItem:
            layerName = item.text(0)
            ZoneName = zoneItem.text(0)
            caption = ('Please set the property of zone ' + ZoneName + ': ' +
                       layerName)
            if self.dlg.rockErosionCheck.checkState() == Qt.Checked:
                useRock = True
            else:
                useRock = False

            try:
                rockType = int(self.dlg.typesOfRockEdit.text())
            except(ValueError):
                rockType = 0
            layerDialog = bedLayer(iface, self.dlg.sediSizeClass.text(),
                                   caption, rockUsed=useRock,
                                   rockTypes=rockType,
                                   presetString=presetString)
            try:
                layerPhys, recString = layerDialog.run()
                item.setText(1, (layerPhys + "; " + recString))
                self.nextLayerpreSet = layerPhys + "; " + recString
            except:
                pass

    def bedLayersExport(self):
        tree = self.dlg.bedLayerTree
        regions = tree.topLevelItemCount()

        layerText = '// Bed Property Spatial Distribution Method (UNI ZON \
POINT)\n'
        if self.dlg.rdoBedUniform.isChecked():
            layerText += 'UNIFORM\n'
        elif self.dlg.rdoBedZonal.isChecked():
            layerText += 'ZONAL\n'
            layerText += '// Bed Gradation Zone Input Method: 2DM File Name\n'
            if self.dlg.sameFileAsFlowBox.isChecked():
                layerText += (self.dlg.lineEditMeshFileName.text() + '\n')
            else:
                layerText += (self.dlg.label_45.text() + '\n')
            layerText += '// Number of Bed Property Zones\n'
            layerText += (str(regions) + '\n')
        else:
            layerText += 'POINT\n'

        if (self.dlg.rdoBedUniform.isChecked() or
                self.dlg.rdoBedZonal.isChecked()):
            for i in range(0, regions):
                bedItem = tree.topLevelItem(i)
                layerText += '// Number of Bed Layers\n'
                layerText += (str(bedItem.childCount()) + '\n')
                if bedItem.childCount() > 0:
                    for j in range(0, bedItem.childCount()):
                        string = bedItem.child(j).text(1)
                        string = re.split(';', string)
                        layerText += '// Thickness Unit(SI/EN) Den_Clay\
(Cohesive) for eachlayer and zone\n'
                        layerText += (string[0] + '\n')
                        layerText += '// FRACTION V1 V2 ... Vsed_nclass for \
each bed layer and bed zone\n'
                        layerText += (string[1] + '\n')
        else:
            layerText += '// File Name for Bed Gradation on Survey Points:\n'
            bedItem = tree.topLevelItem(0)
            fileName = bedItem.text(1)
            layerText += (fileName + '\n')

        layerText += '// Special-Setup-for-Sursurface-Bed-Properties(\
Varying_Thickness, ZEROing_for_Gradation_and_Elevation) (YES or NO)\n'
        layerText += ('NO\n')

        table = self.dlg.bedRockSetTable
        if self.dlg.rockErosionCheck.isChecked():
            for i in range(0, int(self.dlg.typesOfRockEdit.text())):
                layerText += '// Erodible Rock Model Used (REC or STREAM)\n'
                if table.cellWidget(i*2, 0).currentIndex() == 0:
                    layerText += 'RECLAMATION\n'
                    layerText += '// Erodible Rock Properties: d_cover Kh \
Tau_cri Ka Young Tensile\n'
                else:
                    layerText += 'STREAM\n'

                for j in range(1, 5):
                    layerText += (table.item(i*2+1, j).text() + ' ')

                if table.cellWidget(i*2+1, 5):
                    layerText += table.cellWidget(i*2+1, 5).text()
                else:
                    layerText += table.item(i*2+1, 5).text()

                if table.cellWidget(i*2, 0).currentIndex() == 0:
                    layerText += (' ' + table.item(i*2+1, 6).text() + '\n')
                else:
                    layerText += '\n'

        self.layerText = layerText


class bankErosionMod:
    def __init__(self, iface, dialog):
        self.iface = iface
        self.dlg = dialog

        self.dlg.remeshFileSelector.setEnabled(False)
        self.dlg.remeshLabel.setEnabled(False)
        self.bankDepositionMesh = ''

        self.dlg.bankErosionChkBox.stateChanged.connect(self.activateModel)
        self.dlg.solverTabWidget.currentChanged.connect(self.setBankTable)
        caption = u'請選擇岸壁沖蝕後的網格檔案(.2dm)'
        self.dlg.remeshFileSelector.clicked.connect(
            lambda: fileBrowser(self.dlg, caption,
                                self.dlg.saveFolderEdit.text(),
                                self.dlg.remeshLabel, '(*.2dm)'))
        self.dlg.erosionModTable.itemClicked.connect(self.callPopUp)
        self.dlg.remeshZoneChk.stateChanged.connect(self.remeshFileChk)
        self.dlg.bankModBox.currentIndexChanged.connect(self.depositionFile)

    def depositionFile(self):
        idx = self.dlg.bankModBox.currentIndex()
        fileName = ''
        if idx in [1, 2]:
            caption = u'請選擇標示岸壁沖蝕後泥砂移動區域的網格檔(.2dm)(可略過)'
            fileName = fileBrowser(self.dlg, caption,
                                   self.dlg.saveFolderEdit.text(),
                                   presetType='(*.2dm)')
            self.dlg.erosionModTable.setEnabled(False)
        else:
            self.dlg.erosionModTable.setEnabled(True)

        self.bankDepositionMesh = fileName

    def remeshFileChk(self):
        if self.dlg.remeshZoneChk.isChecked():
            self.dlg.remeshFileSelector.setEnabled(True)
            self.dlg.remeshLabel.setEnabled(True)
        else:
            self.dlg.remeshFileSelector.setEnabled(False)
            self.dlg.remeshLabel.setEnabled(False)

    def callPopUp(self):
        c_Row = self.dlg.erosionModTable.currentRow()
        c_Column = self.dlg.erosionModTable.currentColumn()

        if c_Column == 2:
            propWindow = bankProp(self.iface, self.dlg)
            resultString = propWindow.run()
            self.dlg.erosionModTable.item(c_Row, 2).setText(resultString)

    def activateModel(self):
        if self.dlg.bankErosionChkBox.isChecked():
            self.dlg.bankErosionFrameWork.setEnabled(True)
        else:
            self.dlg.bankErosionFrameWork.setEnabled(False)

    def setBankTable(self):
        if self.dlg.solverTabWidget.currentIndex() == 1:
            self.countBank()
            if len(self.banks) % 2 != 0:
                onCritical(130)
        self.dlg.bankTimeStep.setText(self.dlg.lineEditTStep.text())

        self.dlg.bankPairTable.setHorizontalHeaderLabels(['Toe', 'Top'])
        self.dlg.bankPairTable.setColumnCount(2)
        self.dlg.bankPairTable.setColumnWidth(0, 60)
        self.dlg.bankPairTable.setColumnWidth(1, 60)

        self.dlg.erosionModTable.setColumnCount(3)
        self.dlg.erosionModTable.setColumnWidth(1, 120)
        self.dlg.erosionModTable.setColumnWidth(2, 180)

        if self.dlg.erosionModTable.rowCount() == 0:
            try:
                if len(self.banks) >= 2:
                    self.dlg.bankPairTable.setRowCount(
                        int(ceil(len(self.banks)/2.0)))
                    self.dlg.erosionModTable.setRowCount(
                        int(ceil(len(self.banks)/2.0)))
                    for i in range(0, int(ceil(len(self.banks)/2.0))):
                        comboToe = QComboBox()
                        for j in range(0, len(self.banks)):
                            comboToe.addItem(str(self.banks[j]))
                        self.dlg.bankPairTable.setCellWidget(i, 0, comboToe)
                        comboTop = QComboBox()
                        for j in range(0, len(self.banks)):
                            comboTop.addItem(str(self.banks[j]))
                        self.dlg.bankPairTable.setCellWidget(i, 1, comboTop)
                        self.dlg.erosionModTable.setItem(
                            i, 0, QTableWidgetItem('Pair ' + str(i+1)))
                        self.dlg.erosionModTable.setItem(
                            i, 2, QTableWidgetItem('Click to set property'))
                        cohChkBox = QCheckBox()
                        cohChkBox.setText('Cohesive Bank')
                        self.dlg.erosionModTable.setCellWidget(i, 1, cohChkBox)
                else:
                    self.dlg.bankPairTable.setRowCount(1)
                    comboToe = QComboBox()
                    for j in range(0, len(self.banks)):
                        comboToe.addItem(str(self.banks[j]))
                    self.dlg.bankPairTable.setCellWidget(0, 0, comboToe)
                    comboTop = QComboBox()
                    for j in range(0, len(self.banks)):
                        comboTop.addItem(str(self.banks[j]))
                    self.dlg.bankPairTable.setCellWidget(0, 1, comboTop)
                    self.dlg.erosionModTable.setItem(
                        0, 0, QTableWidgetItem('Pair 1'))
                    self.dlg.erosionModTable.setItem(
                        0, 2, QTableWidgetItem('Click to set property'))
                    cohChkBox = QCheckBox()
                    cohChkBox.setText('Cohesive Bank')
                    self.dlg.erosionModTable.setCellWidget(0, 1, cohChkBox)
            except:
                pass
        else:
            rowRequired = int(ceil(len(self.banks)/2.0))
            c_Row = self.dlg.erosionModTable.rowCount()
            if rowRequired > c_Row:
                for i in range(c_Row, rowRequired):
                    comboToe = QComboBox()
                    for j in range(0, len(self.banks)):
                        comboToe.addItem(str(self.banks[j]))
                    comboTop = QComboBox()
                    for j in range(0, len(self.banks)):
                        comboTop.addItem(str(self.banks[j]))

                    self.dlg.bankPairTable.insertRow(i)
                    self.dlg.bankPairTable.setCellWidget(i, 0, comboToe)
                    self.dlg.bankPairTable.setCellWidget(i, 1, comboTop)

                    self.dlg.erosionModTable.insertRow(i)
                    self.dlg.erosionModTable.setItem(
                        i, 0, QTableWidgetItem(u'Pair ' + str(i+1)))
                    self.dlg.erosionModTable.setItem(
                        i, 2, QTableWidgetItem('Click to set property'))
                    cohChkBox = QCheckBox()
                    cohChkBox.setText('Cohesive Bank')
                    self.dlg.erosionModTable.setCellWidget(i, 1, cohChkBox)
            elif rowRequired < c_Row:
                while c_Row > rowRequired:
                    self.dlg.bankPairTable.removeRow(c_Row-1)
                    self.dlg.erosionModTable.removeRow(c_Row-1)

                    c_Row = self.dlg.erosionModTable.rowCount()

    def countBank(self):
        table = self.dlg.boundaryTable
        Rows = table.rowCount()
        banks = list()

        for i in range(0, Rows):
            box = table.cellWidget(i, 1)
            try:
                if box.currentText() == 'BANK':
                    banks.append(i+1)
            except:
                pass
        self.banks = banks

    def bankModelofLineRetreat(self, string):
        string = '// Bank Erosion Module: Pairing IDs of all Bank Zones \
(Toe_ID Top_ID ...)\n'
        string += self.dlg.bankPairTable.cellWidget(0, 0).currentText()
        string += ' '
        string += self.dlg.bankPairTable.cellWidget(0, 1).currentText()
        string += '\n'

        bankMethod = self.dlg.erosionModTable.item(0, 2).text()
        string += '// Bank Erosion Property: Bank_Type(1=non_cohesive) \
lateral_model(1_to_3)\n'
        if not self.dlg.erosionModTable.cellWidget(0, 1).isChecked():
            string += str(1)
        else:
            string += str(2)
        try:
            bankMethod = re.split(';', bankMethod)
            string += ' '
            string += bankMethod[0]
            string += '\n'
            if bankMethod[0] == '1':
                string += '// Non-Cohesive Bank Property: L_to_V Ratio\n'
            elif bankMethod[0] == '2':
                string += '// Non-Cohesive Bank Property: Erodibility(m/s) \
Tau_cri_L(Pa) Exp\n'
            else:
                string += '// Non-Cohesive Bank Property: Tau_cri_L(Pa) \
Tau_cri_V(Pa) )\n'
            string += bankMethod[1]
            string += '\n'
        except:
            onCritical(131)
        # Remesh time interval (Not yet complete, currently fix to 1)
        string += '// Remesh Time Interval for Bank Reterat(in HOUR)\n'
        string += '1\n'

        string += '// 2DM File to define MESH Zone for Remesh? \
(empty-line=NO)\n'
        if self.dlg.remeshZoneChk.isChecked():
            string += (self.dlg.remeshLabel.text() + '\n')
        else:
            string += '\n'

        return string

    def bankModelofFailureMovingMesh(self, string):
        string += '// Bank Erosion Module: n_bank_segment = number of bank \
segments\n'
        string += (str(self.dlg.bankPairTable.rowCount()) + '\n')
        string += '// Bank Erosion Module: Pairing IDs of all Bank Zones \
(Toe_ID Top_ID ...)\n'

        for i in range(0, self.dlg.bankPairTable.rowCount()):
            string += self.dlg.bankPairTable.cellWidget(i, 0).currentText()
            string += ' '
            string += self.dlg.bankPairTable.cellWidget(i, 1).currentText()
            string += ' '
        string = string[:-1] + '\n'

        string += '// 2DM File to define MESH Zone for Bank Depositon? YES, \
below is the file name:\n'
        string += (self.bankDepositionMesh + '\n')
        string += '// 2DM File to define MESH Zone for Remesh? \
(empty-line=NO)\n'
        if self.dlg.remeshZoneChk.isChecked():
            string += (self.dlg.remeshLabel.text() + '\n')
        else:
            string += '\n'
        return string

    def bankModelofFalureBasedFixedMesh(self, string):
        string += '// Bank Erosion Module: n_bank_segment = number of bank \
segments\n'
        string += (str(self.dlg.bankPairTable.rowCount()) + '\n')
        string += '// Bank Erosion Module: Pairing IDs of all Bank Zones \
(Toe_ID Top_ID ...)\n'

        for i in range(0, self.dlg.bankPairTable.rowCount()):
            string += self.dlg.bankPairTable.cellWidget(i, 0).currentText()
            string += ' '
            string += self.dlg.bankPairTable.cellWidget(i, 1).currentText()
            string += ' '
        string = string[:-1] + '\n'

        string += '// 2DM File to define MESH Zone for Bank Depositon? YES, \
below is the file name:\n'
        string += (self.bankDepositionMesh + '\n')

        return string

    def bankModelofLinearFixedMesh(self, string):
        string += '// Bank Erosion Module: n_bank_segment = number of bank \
segments\n'
        string += (str(self.dlg.bankPairTable.rowCount()) + '\n')
        string += '// Bank Erosion Module: Pairing IDs of all Bank Zones \
(Toe_ID Top_ID ...)\n'
        for i in range(0, self.dlg.bankPairTable.rowCount()):
            string += self.dlg.bankPairTable.cellWidget(i, 0).currentText()
            string += ' '
            string += self.dlg.bankPairTable.cellWidget(i, 1).currentText()
            string += ' '
        string = string[:-1] + '\n'

        for i in range(0, self.dlg.erosionModTable.rowCount()):
            modString = self.dlg.erosionModTable.item(i, 2).text()
            modString = modString.split()
            for j in range(0, len(modString)-1):
                string += (modString[j] + ' ')
            string += self.dlg.bankPairTable.cellWidget(i, 0).currentText()
            string += ' '
            string += self.dlg.bankPairTable.cellWidget(i, 1).currentText()
            string += ' '
            string += (modString[-1] + '\n')

        return string

    def bankModelofAoR(self, string):
        string += '// Bank Erosion Module: n_bank_segment = number of bank \
segments\n'
        string += (str(self.dlg.bankPairTable.rowCount()) + '\n')
        string += '// Bank Erosion Module: Pairing IDs of all Bank Zones \
(Toe_ID Top_ID ...)\n'
        for i in range(0, self.dlg.bankPairTable.rowCount()):
            string += self.dlg.bankPairTable.cellWidget(i, 0).currentText()
            string += ' '
            string += self.dlg.bankPairTable.cellWidget(i, 1).currentText()
            string += ' '
        string = string[:-1] + '\n'

        string += '// Angle of Repose for each bank segment with Bank Type 6: \
Ang_Dry Ang_Wet in degree\n'
        for i in range(0, self.dlg.erosionModTable.rowCount()):
            modString = self.dlg.erosionModTable.item(i, 2).text()
            string += modString
            string += '\n'

        return string

    def exportBank(self):
        string = ''
        if self.dlg.bankModBox.currentIndex() == 0:
            string = self.bankModelofLineRetreat(string)
        elif self.dlg.bankModBox.currentIndex() == 1:
            string = self.bankModelofFailureMovingMesh(string)
        elif self.dlg.bankModBox.currentIndex() == 2:
            string = self.bankModelofFalureBasedFixedMesh(string)
        elif self.dlg.bankModBox.currentIndex() == 3:
            string = self.bankModelofLinearFixedMesh(string)
        elif self.dlg.bankModBox.currentIndex() == 4:
            string = self.bankModelofAoR(string)

        return string
