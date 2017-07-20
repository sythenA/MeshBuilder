from PyQt4.QtGui import QComboBox, QTableWidgetItem, QTreeWidgetItem
from PyQt4.QtCore import Qt
from qgis.utils import iface
from commonDialog import fileBrowser, onCritical
from bedLayerSet import bedLayer
from quasiSediOption import quasiSedimentSetting
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
        caption = 'Please choose a 2dm file or msh file'
        self.dlg.selectBedDistriFileBtn.pressed.connect(
            lambda: fileBrowser(self.dlg, caption, self.dlg.projFolder,
                                self.dlg.bedDistriEdit, '(*.2dm *.msh)'))
        self.bedSet = bedSettingModule(self.dlg)
        self.quasiSedi = False
        self.dlg.sediModelingCombo.currentIndexChanged.connect(
            self.sedimentModelingSetting)

    def useTwo2dmFile(self):
        if self.dlg.sameFileAsFlowBox.checkState() == Qt.Unchecked:
            self.dlg.bedDistriEdit.setEnabled(True)
            self.dlg.selectBedDistriFileBtn.setEnabled(True)
            self.dlg.bedDistri2dmConfirm.setEnabled(True)
        else:
            self.dlg.bedDistriEdit.setEnabled(False)
            self.dlg.selectBedDistriFileBtn.setEnabled(False)
            self.dlg.bedDistri2dmConfirm.setEnabled(False)

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

    def bankExport(self):
        bankText = '// BANK Module: OPTION DT_Multiple; [0=NO; 1=User_Supplied;\
 2=Linear_Retreat; 3=Failure Moving Mesh; 4=Failure Fixed Mesh; 5=Linear Fixed \
Mesh; 6=AoR]\n'
        bankText += '\n'
        self.bankText = bankText


class bedSettingModule:
    def __init__(self, dlg):
        self.dlg = dlg
        self.dlg.bedLayerTree.clear()
        self.getPhysRegionFromMain()
        self.dlg.rdoBedUniform.toggled.connect(self.setBedToUniform)
        self.dlg.rdoBedZonal.toggled.connect(self.setBedToZone)
        self.dlg.rockErosionCheck.stateChanged.connect(self.rockAllowed)
        self.dlg.bedDistri2dmConfirm.pressed.connect(self.getBedPhysRegion)
        self.dlg.readMeshBtn.pressed.connect(self.getPhysRegionFromMain)

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
        if self.dlg.bedDistriEdit.text():
            fileName = self.dlg.bedDistriEdit.text()
            if not os.path.isfile(fileName):
                onCritical(125)
            elif fileName.endswith('.2dm'):
                f = open(fileName)
                meshLines = f.readlines()
                physRef, boundsRef = shepred.read2dmMesh(meshLines)
                physRef.sort()
                _physRef = dict()
                for i in range(0, len(physRef)):
                    _physRef.update({i+1: str(physRef[i])})
                self.boundsRef = boundsRef
                self.physRef = _physRef
            elif fileName.endswith('.msh'):
                boundsRef, physRef = shepred.readMshMesh(fileName)
                self.boundsRef = boundsRef
                self.physRef = physRef
        else:
            onCritical(126)

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
                layerText += (self.dlg.bedDistriEdit.text() + '\n')
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
                for j in range(0, bedItem.childCount()):
                    string = bedItem.child(j).text(1)
                    string = re.split(';', string)
                    layerText += '// Thickness Unit(SI/EN) Den_Clay(Cohesive) \
for eachlayer and zone\n'
                    layerText += (string[0] + '\n')
                    layerText += '// FRACTION V1 V2 ... Vsed_nclass for each \
bed layer and bed zone\n'
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
