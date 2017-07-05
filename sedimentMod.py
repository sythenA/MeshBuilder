from PyQt4.QtGui import QComboBox, QTableWidgetItem, QTreeWidgetItem
from PyQt4.QtCore import Qt
from qgis.utils import iface
from commonDialog import fileBrowser, onCritical
from bedLayerSet import bedLayer
import shepred
import os.path


class sedimentModule:
    def __init__(self, dlg):
        self.dlg = dlg
        self.dlg.sediSizeClass.textChanged.connect(self.setGradTable)
        self.dlg.sedimentTab.setCurrentIndex(0)

        self.dlg.rdoWilEqn.toggled.connect(self.setCapToWil)
        self.dlg.rdoMPMEqn.toggled.connect(self.setTableToMPM)
        self.dlg.rdoParkEqn.toggled.connect(self.setTableToParker)
        self.dlg.rdoEHEqn.toggled.connect(self.cleanEqDependentTable)
        self.dlg.rdoYan79Eqn.toggled.connect(self.cleanEqDependentTable)
        self.dlg.rdoYan73Eqn.toggled.connect(self.cleanEqDependentTable)
        self.dlg.rdoWuEqn.toggled.connect(self.setTableToWu)

        self.dlg.checkCohesiveUsed.stateChanged.connect(self.useCohesive)
        self.dlg.cohFallVelCombo.currentIndexChanged.connect(
            self.checkCohFallVel)
        self.dlg.sameFileAsFlowBox.stateChanged.connect(self.useTwo2dmFile)
        caption = 'Please choose a 2dm file or msh file'
        self.dlg.selectBedDistriFileBtn.pressed.connect(
            lambda: fileBrowser(self.dlg, caption, self.dlg.projFolder,
                                self.dlg.bedDistriEdit, '(*.2dm *.msh)'))
        self.bedSet = bedSettingModule(self.dlg)

    def useTwo2dmFile(self):
        if self.dlg.sameFileAsFlowBox.checkState() == Qt.Unchecked:
            self.dlg.bedDistriEdit.setEnabled(True)
            self.dlg.selectBedDistriFileBtn.setEnabled(True)
            self.dlg.bedDistri2dmConfirm.setEnabled(True)
        else:
            self.dlg.bedDistriEdit.setEnabled(False)
            self.dlg.selectBedDistriFileBtn.setEnabled(False)
            self.dlg.bedDistri2dmConfirm.setEnabled(False)

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

    def setCapToWil(self):
        self.dlg.eqDependentTable.clear()
        self.dlg.eqDependentTable.setRowCount(0)
        self.dlg.eqDependentTable.setColumnCount(0)

        self.dlg.eqDependentTable.setRowCount(1)
        self.dlg.eqDependentTable.setColumnCount(3)
        header = ['T1', 'T2', 'D_SAND']
        self.dlg.eqDependentTable.setHorizontalHeaderLabels(header)

        for i in range(0, self.dlg.eqDependentTable.rowCount()):
            for j in range(0, self.dlg.eqDependentTable.columnCount()):
                self.dlg.eqDependentTable.setItem(i, j, QTableWidgetItem(u''))

        self.dlg.eqDependentTable.setItem(0, 0, QTableWidgetItem(u'0.021'))
        self.dlg.eqDependentTable.setItem(0, 1, QTableWidgetItem(u'0.038'))
        self.dlg.eqDependentTable.setItem(0, 2, QTableWidgetItem(u'1.0'))

    def setTableToMPM(self):
        self.dlg.eqDependentTable.clear()
        self.dlg.eqDependentTable.setRowCount(0)
        self.dlg.eqDependentTable.setColumnCount(0)

        self.dlg.eqDependentTable.setRowCount(1)
        self.dlg.eqDependentTable.setColumnCount(1)
        header = ['HF']
        self.dlg.eqDependentTable.setHorizontalHeaderLabels(header)

        for i in range(0, self.dlg.eqDependentTable.rowCount()):
            for j in range(0, self.dlg.eqDependentTable.columnCount()):
                self.dlg.eqDependentTable.setItem(i, j, QTableWidgetItem(u''))
        self.dlg.eqDependentTable.setItem(0, 0, QTableWidgetItem(u'0.0'))

    def setTableToParker(self):
        self.dlg.eqDependentTable.clear()
        self.dlg.eqDependentTable.setRowCount(0)
        self.dlg.eqDependentTable.setColumnCount(0)

        self.dlg.eqDependentTable.setRowCount(1)
        self.dlg.eqDependentTable.setColumnCount(2)
        header = ['THETA', 'HF']
        self.dlg.eqDependentTable.setHorizontalHeaderLabels(header)

        for i in range(0, self.dlg.eqDependentTable.rowCount()):
            for j in range(0, self.dlg.eqDependentTable.columnCount()):
                self.dlg.eqDependentTable.setItem(i, j, QTableWidgetItem(u''))

        self.dlg.eqDependentTable.setItem(0, 0, QTableWidgetItem(u'0.04'))
        self.dlg.eqDependentTable.setItem(0, 1, QTableWidgetItem(u'0.65'))

    def setTableToWu(self):
        self.dlg.eqDependentTable.clear()
        self.dlg.eqDependentTable.setRowCount(0)
        self.dlg.eqDependentTable.setColumnCount(0)

        self.dlg.eqDependentTable.setRowCount(1)
        self.dlg.eqDependentTable.setColumnCount(1)
        header = ['THETA_CRI']
        self.dlg.eqDependentTable.setHorizontalHeaderLabels(header)

        for i in range(0, self.dlg.eqDependentTable.rowCount()):
            for j in range(0, self.dlg.eqDependentTable.columnCount()):
                self.dlg.eqDependentTable.setItem(i, j, QTableWidgetItem(u''))
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
        self.sediGradText = gradString + line

    def sediCapacity(self):
        table = self.dlg.eqDependentTable
        capacityString = '// Sediment Transport Capacity Equation (EH MPM PARK \
WILC WU YANG73 YANG79 TRI BAG KUO AW RIJN USER GAR WRI MIX\n'
        if self.dlg.rdoEHEqn.isChecked():
            capacityString += 'EH\n'
        elif self.dlg.rdoMPMEqn.isChecked():
            capacityString += 'MPM\n'
            capacityString += '// Capacity Equation Hiding Factor (0 to 0.9)\n'
            capacityString = capacityString + table.item(0, 0).text() + '\n'
        elif self.dlg.rdoParkEqn.isChecked():
            capacityString += 'PARKER\n'
            capacityString += '// Capacity Equation Coefficients for Parker \
and/or Seminara (Theta_Critial Hiding Factor)\n'
            capacityString = (capacityString + table.item(0, 0).text() + ' ' +
                              table.item(0, 1).text() + '\n')
        elif self.dlg.rdoYan79Eqn.isChecked():
            capacityString += 'YANG79\n'
        elif self.dlg.rdoYan73Eqn.isChecked():
            capacityString += 'YANG73\n'
        elif self.dlg.rdoWilEqn.isChecked():
            capacityString += 'WILCOCK\n'
            capacityString += '// Wicock Capacity Equation Coefficients: T1 T2 \
d_sand; Theta=T1+(T2-T1)*Exp(-20F_s)\n'
            capacityString += (table.item(0, 0).text() + ' ')
            capacityString += (table.item(0, 1).text() + ' ')
            capacityString += (table.item(0, 2).text() + '\n')
        elif self.dlg.rdoWuEqn.isChecked():
            capacityString += 'WU\n'
            capacityString += '// Wu Capacity Equation Critical Shields Number\
(0.01 to 0.07)\n'
            capacityString += (table.item(0, 0).text() + '\n')

        capacityString += '// Water Temperature (Celsius):\n'
        if self.dlg.watTempEdit.text():
            capacityString += (self.dlg.watTempEdit.text() + '\n')
        else:
            capacityString += ('25.0' + '\n')
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
        cohText += + '// Cohesive Sediment General Properties \
(C_limit(mm),MOD_consolidation)\n'
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
        self.sediGradExport()
        self.sediCapacity()
        self.cohesiveExport()


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
        table.setColumnCount(6)

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
            boundsRef, physRef = shepred.read2dmMesh(main2dmPath)
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
                boundsRef, physRef = shepred.read2dmMesh(fileName)
                self.boundsRef = boundsRef
                self.physRef = physRef
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
                iface.messageBar().pushMessage(physRef[i+1])
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
                                   rockTypes=rockType)
            try:
                layerPhys, recString = layerDialog.run()
                item.setText(1, (layerPhys + "; " + recString))
            except:
                pass
