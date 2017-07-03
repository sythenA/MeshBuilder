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
        header = ['T1', 'T2', 'D_SAND']
        self.dlg.eqDependentTable.setHorizontalHeaderLabels(header)
        self.dlg.eqDependentTable.setRowCount(1)
        self.dlg.eqDependentTable.setColumnCount(3)

        for i in range(0, self.dlg.eqDependentTable.rowCount()):
            for j in range(0, self.dlg.eqDependentTable.columnCount()):
                self.dlg.eqDependentTable.setItem(i, j, QTableWidgetItem(u''))

        self.dlg.eqDependentTable.setItem(0, 0, QTableWidgetItem(u'0.021'))
        self.dlg.eqDependentTable.setItem(0, 1, QTableWidgetItem(u'0.038'))
        self.dlg.eqDependentTable.setItem(0, 2, QTableWidgetItem(u'1.0'))

    def setTableToMPM(self):
        self.dlg.eqDependentTable.clear()
        header = ['HF']
        self.dlg.eqDependentTable.setHorizontalHeaderLabels(header)
        self.dlg.eqDependentTable.setRowCount(1)
        self.dlg.eqDependentTable.setColumnCount(1)

        for i in range(0, self.dlg.eqDependentTable.rowCount()):
            for j in range(0, self.dlg.eqDependentTable.columnCount()):
                self.dlg.eqDependentTable.setItem(i, j, QTableWidgetItem(u''))
        self.dlg.eqDependentTable.setItem(0, 0, QTableWidgetItem(u'0.0'))

    def setTableToParker(self):
        self.dlg.eqDependentTable.clear()
        header = ['THETA', 'HF']
        self.dlg.eqDependentTable.setHorizontalHeaderLabels(header)
        self.dlg.eqDependentTable.setRowCount(1)
        self.dlg.eqDependentTable.setColumnCount(2)

        for i in range(0, self.dlg.eqDependentTable.rowCount()):
            for j in range(0, self.dlg.eqDependentTable.columnCount()):
                self.dlg.eqDependentTable.setItem(i, j, QTableWidgetItem(u''))

        self.dlg.eqDependentTable.setItem(0, 0, QTableWidgetItem(u'0.04'))
        self.dlg.eqDependentTable.setItem(0, 1, QTableWidgetItem(u'0.05'))

    def setTableToWu(self):
        self.dlg.eqDependentTable.clear()
        header = ['THETA_CRI']
        self.dlg.eqDependentTable.setHorizontalHeaderLabels(header)
        self.dlg.eqDependentTable.setRowCount(1)
        self.dlg.eqDependentTable.setColumnCount(1)

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
        else:
            self.dlg.cohDiaLimEdit.setEnabled(False)
            self.dlg.cohFallVelCombo.setEnabled(False)
            self.dlg.cohSediEroRateGroup.setEnabled(False)
            self.dlg.cohSediDepRateGroup.setEnabled(False)


class bedSettingModule:
    def __init__(self, dlg):
        self.dlg = dlg
        self.getPhysRegionFromMain()
        self.dlg.rdoBedUniform.toggled.connect(self.setBedToUniform)
        self.dlg.rdoBedZonal.toggled.connect(self.setBedToZone)
        self.dlg.rockErosionCheck.stateChanged.connect(self.rockAllowed)

    def rockAllowed(self):
        if self.dlg.rockErosionCheck.checkState() == Qt.Checked:
            self.dlg.typesOfRockEdit.setEnabled(True)
        else:
            self.dlg.typesOfRockEdit.setEnabled(False)

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
                item.setText(0, physRef[i+1])
                self.dlg.bedLayerTree.addTopLevelItem(item)
                self.dlg.zoneBedSelector.addItem(str(i+1))
            self.dlg.bedLayerTree.setColumnWidth(0, 150)
            self.dlg.layerInZoneEdit.textChanged.connect(self.setBedLayerInZone)
            self.dlg.bedLayerTree.itemClicked.connect(self.bedLayerPopUp)
        else:
            onCritical(107)

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
