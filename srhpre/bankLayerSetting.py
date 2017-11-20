import os
from PyQt4 import uic
from PyQt4.QtGui import QDialog, QTableWidgetItem
from copy import deepcopy
from commonDialog import onCritical


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'bankLayer.ui'))


class genBankLayerPropDiag(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(genBankLayerPropDiag, self).__init__(parent)
        self.setupUi(self)


class layerItem:
    def __init__(self, sedimentGrad=list()):
        self.minElev = 0.0  # Minimum Elevation
        self.porosity = 0.0  # Porosity
        self.ssw = 0.0  # Saturated Unit Weight
        self.tau = 0.0  # Critical Shear Stress
        self.coh = 0.0  # Effective Cohesion
        self.phi = 0.0  # Internal Friction Angle
        self.phib = 0.0  # Rate of Pore Water Suction
        self.gradList = sedimentGrad


class bankPairItem:
    def __init__(self, bankLayers, gradList=list()):
        self.grdWatLvl = -999  # Ground Water Elevation
        # -999 to deactivate cohesive banks.
        self.layers = bankLayers
        self.startCSType = 'Fixed'
        self.gradList = gradList
        self.makeLayers()

    def makeLayers(self):
        self.layerItems = list()
        for i in range(0, self.layers):
            self.layerItems.append(layerItem(deepcopy(self.gradList)))


class bankLayerProp:
    def __init__(self, iface, bankPairs, bankLayers, gradClass):
        self.iface = iface
        self.dlg = genBankLayerPropDiag()
        for i in range(0, len(gradClass)):
            gradClass[i].append(0.0)
        self.gradClass = gradClass
        self.makeBankPair(bankPairs, bankLayers)
        self.initGradTable()

        self.dlg.grdWatLvlEdit.editingFinished.connect(self.setPairGrdWatLvl)
        self.dlg.totalLayersEdit.editingFinished.connect(self.makeLayerItem)
        self.dlg.minElevEdit.editingFinished.connect(self.setMinElevLvl)
        self.dlg.porosityEdit.editingFinished.connect(self.setPorosity)
        self.dlg.satWeightEdit.editingFinished.connect(self.setSatWeight)
        self.dlg.tauCriEdit.editingFinished.connect(self.setTauCri)
        self.dlg.effCohEdit.editingFinished.connect(self.setEffCoh)
        self.dlg.phiBEdit.editingFinished.connect(self.setPhiB)
        self.dlg.angEdit.editingFinished.connect(self.setInternalAng)
        self.dlg.pairSelector.currentIndexChanged.connect(self.changePair)
        self.dlg.layerSelector.currentIndexChanged.connect(self.selectLayer)
        self.dlg.sediGradTable.itemEntered.connect(self.setLayerGrad)
        self.dlg.noMoveBtn.toggled.connect(self.setToFixed)
        self.dlg.retreatBtn.toggled.connect(self.setToRetreat)

    def initGradTable(self):
        table = self.dlg.sediGradTable
        if self.gradClass:
            table.setRowCount(2)
            table.setColumnCount(len(self.gradClass))
            for i in range(0, 2):
                for j in range(0, len(self.gradClass)):
                    table.setItem(i, j, QTableWidgetItem())

            for j in range(0, len(self.gradClass)):
                minSize, maxSize, portion = self.gradClass[j]
                table.item(0, j).setText(str(minSize) + ' - ' + str(maxSize))
                table.item(1, j).setText(str(portion))
        self.showContent()

    def run(self):
        result = self.dlg.exec_()
        if result == 1:
            return self.bankPairs
        else:
            onCritical(134)

    def makeBankPair(self, bankPairs, layers):
        for i in range(0, bankPairs):
            self.dlg.pairSelector.addItem(str(i+1))

        self.bankPairs = list()
        for i in range(0, bankPairs):
            self.bankPairs.append(bankPairItem(layers, self.gradClass))
        self.currentPair = self.bankPairs[0]
        self.dlg.grdWatLvlEdit.setText(str(self.currentPair.grdWatLvl))
        for i in range(0, layers):
            self.dlg.layerSelector.addItem(str(i+1))
        self.dlg.totalLayersEdit.setText(str(layers))
        self.dlg.layerSelector.setCurrentIndex(0)

    def setLayerGrad(self):
        idx = self.dlg.layerSelector.currentIndex()
        currentLayer = self.currentPair.layerItems[idx]

        table = self.dlg.sediGradTable
        for j in range(0, table.columnCount()):
            currentLayer.gradList[j][2] = float(table.item(1, j).text())
        self.currentPair.layerItems[idx] = currentLayer

    def showLayerComposition(self):
        table = self.dlg.sediGradTable

        idx = self.dlg.layerSelector.currentIndex()
        currentLayer = self.currentPair.layerItems[idx]
        self.iface.messageBar().pushMessage(str(currentLayer.gradList))
        for j in range(0, len(currentLayer.gradList)):
            item = table.item(1, j)
            item.setText(str(currentLayer.gradList[j][2]))
            table.setItem(1, j, item)

    def setStartType(self):
        idx = self.dlg.pairSelector.currentIndex()
        if self.bankPairs[idx].startCSType == 'Fixed':
            self.dlg.noMoveBtn.setChecked(True)
        else:
            self.dlg.noMoveBtn.setChecked(False)

        if self.bankPairs[idx].startCSType == 'Retreat':
            self.dlg.retreatBtn.setChecked(True)
        else:
            self.dlg.retreatBtn.setChecked(False)

    def changePair(self):
        idx = self.dlg.pairSelector.currentIndex()
        self.currentPair = self.bankPairs[idx]

        bankLayers = self.currentPair.layers
        self.dlg.layerSelector.clear()
        for j in range(0, bankLayers):
            self.dlg.layerSelector.addItem(str(j+1))
        self.dlg.layerSelector.setCurrentIndex(0)
        self.dlg.grdWatLvlEdit.setText(str(self.currentPair.grdWatLvl))
        self.showContent()

    def setPairGrdWatLvl(self):
        self.currentPair.grdWatLvl = float(self.dlg.grdWatLvlEdit.text())
        if self.grdWatLvl == -999.0:
            self.dlg.phiBEdit.setEnabled(False)
            self.dlg.effCohEdit.setEnabled(False)
        else:
            self.dlg.phiBEdit.setEnabled(True)
            self.dlg.effCohEdit.setEnabled(True)

    def setPorosity(self):
        idx = self.dlg.layerSelector.currentIndex()
        currentItem = self.currentPair.layerItems[idx]
        currentItem.porosity = float(self.dlg.porosityEdit.text())
        self.currentPair.layerItems[idx] = currentItem
        self.showContent()

    def setMinElevLvl(self):
        idx = self.dlg.layerSelector.currentIndex()
        currentItem = self.currentPair.layerItems[idx]
        currentItem.minElev = float(self.dlg.minElevEdit.text())
        self.currentPair.layerItems[idx] = currentItem
        self.showContent()

    def setSatWeight(self):
        idx = self.dlg.layerSelector.currentIndex()
        currentItem = self.currentPair.layerItems[idx]
        currentItem.ssw = float(self.dlg.satWeightEdit.text())
        self.currentPair.layerItems[idx] = currentItem
        self.showContent()

    def setTauCri(self):
        idx = self.dlg.layerSelector.currentIndex()
        currentItem = self.currentPair.layerItems[idx]
        currentItem.tau = float(self.dlg.tauCriEdit.text())
        self.currentPair.layerItems[idx] = currentItem
        self.showContent()

    def setEffCoh(self):
        idx = self.dlg.layerSelector.currentIndex()
        currentItem = self.currentPair.layerItems[idx]
        currentItem.coh = float(self.dlg.effCohEdit.text())
        self.currentPair.layerItems[idx] = currentItem
        self.showContent()

    def setPhiB(self):
        idx = self.dlg.layerSelector.currentIndex()
        currentItem = self.currentPair.layerItems[idx]
        currentItem.coh = float(self.dlg.phiBEdit.text())
        self.currentPair.layerItems[idx] = currentItem
        self.showContent()

    def setInternalAng(self):
        idx = self.dlg.layerSelector.currentIndex()
        currentItem = self.currentPair.layerItems[idx]
        currentItem.phi = float(self.dlg.angEdit.text())
        self.currentPair.layerItems[idx] = currentItem
        self.showContent()

    def makeLayerItem(self):
        try:
            self.dlg.layerSelector.clear()
            totalLayers = int(self.dlg.totalLayersEdit.text())
            self.currentPair.layers = totalLayers
            self.currentPair.makeLayers()

            for i in range(0, totalLayers):
                self.dlg.layerSelector.addItem(str(i+1))

        except:
            onCritical(135)

    def selectLayer(self):
        idx = self.dlg.layerSelector.currentIndex()
        self.currentItem = self.currentPair.layerItems[idx]
        self.showContent()

    def setToFixed(self):
        idx = self.dlg.pairSelector.currentIndex()
        self.bankPairs[idx].startCSType = 'Fixed'

    def setToRetreat(self):
        idx = self.dlg.pairSelector.currentIndex()
        self.bankPairs[idx].startCSType = 'Retreat'

    def showContent(self):
        idx = self.dlg.layerSelector.currentIndex()
        currentItem = self.currentPair.layerItems[idx]

        if self.currentPair.grdWatLvl == -999.0:
            self.dlg.phiBEdit.setEnabled(False)
            self.dlg.effCohEdit.setEnabled(False)
        else:
            self.dlg.phiBEdit.setEnabled(True)
            self.dlg.effCohEdit.setEnabled(True)

        self.setStartType()
        self.showLayerComposition()
        self.dlg.minElevEdit.setText(str(currentItem.minElev))
        self.dlg.porosityEdit.setText(str(currentItem.porosity))
        self.dlg.satWeightEdit.setText(str(currentItem.ssw))
        self.dlg.tauCriEdit.setText(str(currentItem.tau))
        self.dlg.effCohEdit.setText(str(currentItem.coh))
        self.dlg.angEdit.setText(str(currentItem.phi))
        self.dlg.phiBEdit.setText(str(currentItem.phib))
