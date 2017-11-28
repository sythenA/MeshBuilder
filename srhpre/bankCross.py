import os
import re
from math import sqrt
from operator import itemgetter
from qgis.core import QgsVectorLayer, QgsMapLayerRegistry, QgsVectorFileWriter
from qgis.core import QgsFields, QgsField, QgsGeometry, QgsFeature, QGis
from qgis.core import QgsFeatureRequest, QgsExpression
from PyQt4 import uic
from PyQt4.QtGui import QDialog, QListWidgetItem, QTableWidgetItem
from PyQt4.QtCore import QVariant, Qt
from copy import copy
import subprocess


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'bankCrossSection.ui'))


class bankCrossSecDiag(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(bankCrossSecDiag, self).__init__(parent)
        self.setupUi(self)


def breakNS(nodeString):
    boundaries = list()
    boundary = list()
    for i in range(0, len(nodeString)):
        if int(nodeString[i]) >= 0:
            boundary.append(int(nodeString[i]))
        else:
            boundary.append(-int(nodeString[i]))
            boundaries.append(boundary)
            boundary = list()
    return boundaries


class bankCross:
    def __init__(self, meshPath, toe, top, jump):
        self.readMesh(meshPath, toe, top)
        self.setEndNodes(jump)

    def readMesh(self, meshPath, toe, top):
        f = open(meshPath, 'r')
        dat = f.readlines()
        id_list = list()
        nodes = dict()
        NodeString = list()
        mesh_list = list()

        for line in dat:
            lineSeg = re.split('\s+|\t', line.strip())
            if lineSeg[0] == 'ND':
                id_list.append([int(lineSeg[1]), float(lineSeg[2]),
                                float(lineSeg[3])])
                nodes.update({int(lineSeg[1]):
                              (float(lineSeg[2]), float(lineSeg[3]),
                               float(lineSeg[4]))})
            elif lineSeg[0] == 'NS':
                for j in range(1, len(lineSeg)):
                    NodeString.append(int(lineSeg[j]))
            elif lineSeg[0] == 'E3T' or lineSeg[0] == 'E4Q':
                mesh_list.append(lineSeg[1:-1])

        for i in range(0, len(mesh_list)):
            for j in range(0, len(mesh_list[i])):
                mesh_list[i][j] = int(mesh_list[i][j])

        boundaries = breakNS(NodeString)

        Toes = list()
        for number in toe:
            Toes.append(boundaries[number-1])
        Tops = list()
        for number in top:
            Tops.append(boundaries[number-1])

        self.node_ids = id_list
        self.nodes = nodes
        self.elements = mesh_list
        self.Toes = Toes
        self.Tops = Tops

    def setEndNodes(self, jump):
        Toe_Ids = list()
        Top_Ids = list()
        last_toe = list()
        last_top = list()
        bank_pair_num = list()
        for i in range(0, len(self.Tops)):
            tops = list()
            for j in range(0, len(self.Tops[i]), jump):
                tops.append(self.Tops[i][j])
                bank_pair_num.append(i+1)

            if self.Tops[i][-1] not in tops:
                tops.append(self.Tops[i][-1])
                bank_pair_num.append(i+1)
            Top_Ids.append(tops)
            last_top.append(self.Tops[i][-1])

        for i in range(0, len(self.Toes)):
            toes = list()
            for j in range(0, len(self.Toes[i]), jump):
                toes.append(self.Toes[i][j])
            if self.Toes[i][-1] not in toes:
                toes.append(self.Toes[i][-1])
            Toe_Ids.append(toes)
            last_toe.append(self.Toes[i][-1])

        pair = zip(Toe_Ids, Top_Ids)
        for i in range(0, len(pair)):
            pair[i] = zip(pair[i][0], pair[i][1])

        self.twoEnds = pair
        self.last_toe = last_toe
        self.last_top = last_top
        self.bank_pair_num = bank_pair_num

    def findNear(self, point_id):
        x = self.nodes[point_id][0]
        y = self.nodes[point_id][1]

        dist_list = list()
        for i in range(0, len(self.node_ids)):
            if self.node_ids[i][0] != point_id:
                xp = self.node_ids[i][1]
                yp = self.node_ids[i][2]
                dist = sqrt((x - xp)**2 + (y - yp)**2)
                dist_list.append([self.node_ids[i][0], dist])
        dist_list = sorted(dist_list, key=itemgetter(1))

        return dist_list[0:20]

    def distToTwoEnds(self, endPoints, nodes, stP):
        x1 = self.nodes[endPoints[0]][0]
        y1 = self.nodes[endPoints[0]][1]
        x2 = self.nodes[endPoints[1]][0]
        y2 = self.nodes[endPoints[1]][1]

        stPx = self.nodes[stP][0]
        stPy = self.nodes[stP][1]

        node_dist = list()
        for node in nodes:
            node_x = self.nodes[node[0]][0]
            node_y = self.nodes[node[0]][1]

            dist = (sqrt((node_x-x1)**2 + (node_y-y1)**2) +
                    sqrt((node_x-x2)**2 + (node_y-y2)**2) +
                    sqrt((node_x - stPx)**2 + (node_y - stPy)**2))
            node_dist.append([node[0], dist])

        node_dist = sorted(node_dist, key=itemgetter(1))

        return node_dist

    def findBetween(self):
        banList = list()
        for bank in self.twoEnds:
            for pair in bank:
                banList.append(pair[0])

        CSs = list()
        crossSection = list()
        for bank in self.twoEnds:
            for pair in bank:
                stP = pair[0]
                crossSection.append(stP)
                enP = ''
                while enP != pair[1]:
                    node_dist = self.findNear(stP)
                    node_dist = self.distToTwoEnds(pair, node_dist, stP)
                    n_list = list()
                    for node in node_dist:
                        if node[0] not in banList:
                            n_list.append(node)
                    if n_list:
                        crossSection.append(n_list[0][0])
                        banList.append(n_list[0][0])
                        enP = n_list[0][0]
                        stP = enP
                CSs.append(crossSection)
                crossSection = list()

        self.CS = CSs

    def nodeInElement(self, node1, node2, element):
        element.pop(0)
        element.append(element[0])

        for i in range(0, len(element)-1):
            if element[i:i+2] == [node1, node2]:
                if i > 0 and i != len(element)-2:
                    return element[i-1]
                elif i == 0:
                    return element[-2]
                else:
                    return element[-3]
            elif element[i:i+2] == [node2, node1]:
                if node1 != element[-1]:
                    return element[i+2]
                else:
                    return element[1]

    def findOutSide(self):
        CS = self.CS
        banList = list()
        for bank in CS:
            banList += bank

        for bank in CS:
            for toe in self.Toes:
                try:
                    idx = toe.index(bank[0])

                    if bank[0] not in self.last_toe:
                        nextOnToe = toe[idx+1]
                        for element in self.elements:
                            if bank[0] in element and nextOnToe in element:
                                tarNode = self.nodeInElement(
                                    bank[0], nextOnToe, element)
                                if tarNode and tarNode not in banList:
                                    bank.insert(0, tarNode)
                    else:
                        lastOnToe = toe[idx-1]
                        for element in self.elements:
                            if bank[0] in element and lastOnToe in element:
                                tarNode = self.nodeInElement(
                                    bank[0], lastOnToe, element)
                                if tarNode and tarNode not in banList:
                                    bank.insert(0, tarNode)
                except:
                    pass

            for top in self.Tops:
                try:
                    idx = top.index(bank[-1])

                    if bank[-1] not in self.last_top:
                        nextOnTop = top[idx+1]
                        for element in self.elements:
                            if bank[-1] in element and nextOnTop in element:
                                tarNode = self.nodeInElement(
                                    bank[-1], nextOnTop, element)
                                if tarNode and tarNode not in banList:
                                    bank.append(tarNode)
                    else:
                        lastOnTop = top[idx-1]
                        for element in self.elements:
                            if bank[-1] in element and lastOnTop in element:
                                tarNode = self.nodeInElement(
                                    bank[-1], lastOnTop, element)
                                if tarNode and tarNode not in banList:
                                    bank.append(tarNode)
                except:
                    pass


class bankCrossSecSetting:
    def __init__(self, iface, projFolder, nodePath, boundaryPath, bankPairs,
                 bankCS):
        self.iface = iface
        self.projFolder = projFolder
        self.dlg = bankCrossSecDiag(parent=iface.mainWindow())
        self.nodePath = nodePath
        self.boundaryPath = boundaryPath
        self.loadLayer()
        self.bankCS = bankCS
        self.bankPairs = bankPairs
        self.loadCrossSecs()

        self.dlg.retreatRdo.clicked.connect(self.setToRetreatCS)
        self.dlg.noMoveRdo.clicked.connect(self.setToFixedCS)
        self.dlg.sectionList.itemClicked.connect(self.showSec)

    def run(self):
        self.dlg.show()
        result = self.dlg.exec_()
        if result:
            pass

    def checkFolder(self):
        folderPath = os.path.join(self.projFolder, 'MeshShp', 'bank')
        if not os.path.isdir(folderPath):
            subprocess.Popen(['mkdir', folderPath])

    def loadCrossSecs(self):
        if self.bankCS:
            bankCS = self.bankCS
            pairNum = self.bankCS.bank_pair_num
            bankPairs = self.bankPairs  # Cross-section data

            for sec in bankCS.CS:
                bankSecItem = bankCSListItem(self.dlg.sectionList,
                                             self.mNodeLayer, sec)
                idx = bankCS.CS.index(sec)
                bankSecItem.pairNum = pairNum[idx]
                bankSecItem.bankData = copy(bankPairs[bankSecItem.pairNum-1])
                if idx >= 1:
                    if (pairNum[idx] != pairNum[idx-1] and
                            bankPairs[bankSecItem.pairNum-1].startCSType ==
                            'Fixed'):
                        bankSecItem.Type = 'Fixed'
                else:
                    if bankPairs[0].startCSType == 'Fixed':
                        bankSecItem.Type = 'Fixed'

                bankSecItem.setText('bank Cross-Section ' + str(idx+1).zfill(2))
                bankSecItem.genText()
                self.dlg.sectionList.addItem(bankSecItem)

    def loadMeshNodes(self):
        self.checkFolder()
        f = open(self.mesh, 'r')
        dat = f.readlines()
        f.close()

        nodePath = os.path.join(self.projFolder, 'MeshShp', 'bank',
                                'bankNodes.shp')
        boundaryPath = os.path.join(self.projFolder, 'MeshShp', 'bank',
                                    'boundaries.shp')
        nodeFields = QgsFields()
        nodeFields.append(QgsField('id', QVariant.Int))
        nodeFields.append(QgsField('z', QVariant.Double))
        NodeWriter = QgsVectorFileWriter(nodePath, 'utf-8', nodeFields,
                                         QGis.WKBPoint, self.crs,
                                         "ESRI Shapefile")
        boundaryFields = QgsFields()
        boundaryFields.append(QgsField('start_id', QVariant.Int))
        boundaryFields.append(QgsField('end_id', QVariant.Int))
        boundaryFields.append(QgsField('string No', QVariant.Int))

        NSlist = list()
        nodeDict = dict()
        for line in dat:
            line = re.split('\s+|\t', line)
            line.pop(-1)
            if line[0] == 'ND':
                feature = QgsFeature()
                geoString = 'POINT(' + line[2] + ' ' + line[3] + ')'
                feature.setGeometry(QgsGeometry().fromWkt(geoString))
                feature.setAttributes([int(line[1]), float(line[4])])
                NodeWriter.addFeature(feature)
                nodeDict.update({int(line[1]): (line[2], line[3])})
            elif line[0] == 'NS':
                line.pop(0)
                NSlist += line

        del NodeWriter

        boundaries = breakNS(NSlist)
        boundaryWriter = QgsVectorFileWriter(boundaryPath, 'utf-8',
                                             boundaryFields, QGis.WKBLineString,
                                             self.crs, 'ESRI Shapefile')
        for i in range(0, len(boundaries)):
            feature = QgsFeature()
            geoString = 'LINESTRING('
            for j in range(0, len(boundaries[i])):
                node_id = boundaries[i][j]
                (x, y) = nodeDict[node_id]
                geoString += str(x) + ' ' + str(y) + ','
            geoString = geoString[:-1]
            geoString += ')'
            feature.setGeometry(QgsGeometry().fromWkt(geoString))
            feature.setAttributes([boundaries[i][0], boundaries[i][-1], i+1])
            boundaryWriter.addFeature(feature)

        del boundaryWriter
        self.nodePath = nodePath
        self.boundaryPath = boundaryPath

    def loadLayer(self):
        nodePath = self.nodePath
        boundaryPath = self.boundaryPath

        nodeLayer = QgsVectorLayer(nodePath, 'Nodes', 'ogr')
        boundaryLayer = QgsVectorLayer(boundaryPath, 'boundary', 'ogr')
        mBoundaryLayer = QgsMapLayerRegistry.instance().addMapLayer(
            boundaryLayer)
        mNodeLayer = QgsMapLayerRegistry.instance().addMapLayer(nodeLayer)
        self.mNodeLayer = mNodeLayer
        self.iface.setActiveLayer(mNodeLayer)

    def showSec(self, Type='Move'):
        # Select cross-section and show on map.
        self.dlg.setWindowModality(Qt.NonModal)
        bankItem = self.dlg.sectionList.currentItem()
        bankItem.selectByNode()
        if bankItem.Type == 'Fixed':
            self.showPropOnTable(bankItem.bankData, 'Fixed')
        else:
            self.showPropOnTable(bankItem.bankData, Type)
        self.showTextofBank()

    def setToFixedCS(self):
        bankItem = self.dlg.sectionList.currentItem()
        if bankItem:
            bankItem.Type = 'Fixed'
            self.showSec()

    def setToRetreatCS(self):
        bankItem = self.dlg.sectionList.currentItem()
        if bankItem:
            bankItem.Type = 'Move'
            self.showSec()

    def showPropOnTable(self, bankSecData, Type='Move'):
        if Type == 'Fixed':
            self.dlg.noMoveRdo.setChecked(True)
        else:
            self.dlg.retreatRdo.setChecked(True)
        table = self.dlg.sectionPropTable
        table.clear()

        n_layers = len(bankSecData.layerItems)
        table.setRowCount(2*n_layers+2)

        layerData = bankSecData.layerItems[0]
        if len(bankSecData.gradList) > 8:
            table.setColumnCount(len(layerData.gradList))
        else:
            table.setColumnCount(8)

        table.setRowHeight(0, 60)

        item = QTableWidgetItem('MinElev')
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        table.setItem(0, 0, item)
        item = QTableWidgetItem('Ground\n Water\n Level')
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        table.setItem(0, 1, item)
        item = QTableWidgetItem('Porosity')
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        table.setItem(0, 2, item)
        item = QTableWidgetItem('Saturated\n SW')
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        table.setItem(0, 3, item)
        item = QTableWidgetItem('Erodibility')
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        table.setItem(0, 4, item)
        item = QTableWidgetItem('Effective\n cohesion')
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        table.setItem(0, 5, item)
        item = QTableWidgetItem('Internal\n friction\n angle')
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        table.setItem(0, 6, item)
        item = QTableWidgetItem('Suction\n stress\n angle')
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        table.setItem(0, 7, item)

        for k in range(0, len(bankSecData.gradList)):
            item = QTableWidgetItem(str(bankSecData.gradList[k][0]) + ' - ' +
                                    str(bankSecData.gradList[k][1]) + ' mm')
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            table.setItem(n_layers+1, k, item)

        for i in range(1, n_layers+1):
            layerData = bankSecData.layerItems[i-1]
            table.setItem(i, 0, QTableWidgetItem(str(layerData.minElev)))
            table.setItem(i, 1, QTableWidgetItem(str(layerData.grdWatLvl)))
            table.setItem(i, 2, QTableWidgetItem(str(layerData.porosity)))
            table.setItem(i, 3, QTableWidgetItem(str(layerData.ssw)))
            table.setItem(i, 4, QTableWidgetItem(str(layerData.erodibility)))
            table.setItem(i, 5, QTableWidgetItem(str(layerData.coh)))
            table.setItem(i, 6, QTableWidgetItem(str(layerData.phi)))
            table.setItem(i, 7, QTableWidgetItem(str(layerData.phib)))

            for j in range(0, len(layerData.gradList)):
                item2 = QTableWidgetItem(str(layerData.gradList[j][2]))
                table.setItem(n_layers+2-1+i, j, item2)

    def secPropTableToItem(self):
        table = self.dlg.sectionPropTable
        bankItem = self.dlg.sectionList.currentItem()
        n_layers = len(bankItem.bankData.layerItems)

        for i in range(0, n_layers):
            idx = i+1
            layerItem = bankItem.bankData.layerItems[i]
            layerItem.minElev = float(table.item(idx, 0).text())
            layerItem.grdWatLvl = float(table.item(idx, 1).text())
            layerItem.porosity = float(table.item(idx, 2).text())
            layerItem.ssw = float(table.item(idx, 3).text())
            layerItem.erodibility = float(table.item(idx, 4).text())
            layerItem.coh = float(table.item(idx, 5).text())
            layerItem.phi = float(table.item(idx, 6).text())
            layerItem.phib = float(table.item(idx, 7).text())

            for j in range(0, len(layerItem.gradList)):
                item = table.item(n_layers+2+i, j)
                layerItem.gradList[j][2] = float(item.text())

        self.showSec()

    def nodeInTop(self, secNodes):
        Tops = self.bankCS.Tops

        for node in secNodes:
            for i in range(0, len(Tops)):
                if node in Tops[i]:
                    x, y, z = self.querryEl(node)
                    return [node, x, y, z]

    def nodeInToe(self, secNodes):
        Toes = self.bankCS.Toes

        for node in secNodes:
            for i in range(0, len(Toes)):
                if node in Toes[i]:
                    x, y, z = self.querryEl(node)
                    return [node, x, y, z]

    def querryEl(self, node):
        layer = QgsMapLayerRegistry.instance().mapLayer(self.mNodeLayer.id())
        querryString = "id=" + str(node)
        expr = QgsExpression(querryString)
        feats = layer.getFeatures(QgsFeatureRequest(expr))
        for feat in feats:
            x = feat.geometry().asQPointF().x()
            y = feat.geometry().asQPointF().y()
            z = feat['z']
        return [x, y, z]

    def inverseList(self, _input):
        _output = list()
        for i in range(0, len(_input)):
            _output.append(_input[len(_input)-1-i])
        return _output

    def secDistances(self, CSNodes):
        CSNodeList = list()
        x0, y0, z0 = self.querryEl(CSNodes[0])
        CSNodeList.append([0.0, z0])
        for i in range(1, len(CSNodes)):
            x, y, z = self.querryEl(CSNodes[i])
            dist = sqrt((x-x0)**2 + (y-y0)**2)
            CSNodeList.append([dist, z])
        return CSNodeList

    def showTextofBank(self):
        bankItem = self.dlg.sectionList.currentItem()
        textString = ''
        textString += '// ****************************************************'
        textString += '*******\n'
        textString += '// * Bank_Profile ID (consecutive please): Segment_ID= '
        textString += str(bankItem.pairNum) + '\n'
        textString += '// *****************************************************'
        textString += '******\n'
        rowId = self.dlg.sectionList.row(bankItem)
        textString += 'BANK_ID   ' + str(rowId+1) + '\n'
        textString += '// Bank Type: NO_MOVE or RETREAT\n'
        if bankItem.Type == 'Fixed':
            textString += 'BANK_TYPE NO_MOVE\n'
            textString += '// Top point (x y) coordinates used by SRH-2D mesh '
            textString += '(units the same as the mesh)\n'
            CSNodes = bankItem.bankNodes
            CSNodes = self.inverseList(CSNodes)
            node, x, y, z = self.nodeInTop(CSNodes)
            line = 'TOP_XY     '
            line += '{0:15E}'.format(x)
            line += '     '
            line += ('{0:15E}'.format(y) + '\n')
            textString += line
            textString += '// Toe point (x y) coordinates used by SRH-2D mesh '
            textString += '(units the same as the mesh)\n'
            node, x, y, z = self.nodeInToe(CSNodes)
            line = 'TOE_XY     '
            line += '{0:15E}'.format(x)
            line += '     '
            line += ('{0:15E}'.format(y) + '\n')
            textString += line
        else:
            textString += 'BANK_TYPE RETREAT\n'
            textString += (
                '// Top point (x y) coordinates used by SRH-2D mesh ')
            textString += '(units the same as the mesh)\n'
            CSNodes = bankItem.bankNodes
            topNode, x, y, z = self.nodeInTop(CSNodes)
            line = 'TOP_XY     '
            line += '{0:15E}'.format(x)
            line += '     '
            line += ('{0:15E}'.format(y) + '\n')
            textString += line
            textString += ('// Toe point (x y) coordinates used by SRH-2D mesh')
            textString += ' units the same as the mesh)\n'
            toeNode, x, y, z = self.nodeInToe(CSNodes)
            line = 'TOE_XY     '
            line += '{0:15E}'.format(x)
            line += '     '
            line += ('{0:15E}'.format(y) + '\n')
            textString += line
            textString += '// Number of points on the bank profile '
            textString += '(from Top to Toe)\n'
            textString += ('N_NODE    ' + str(len(CSNodes)) + '\n')
            textString += ('// List of (d elevation) for each point in meter\n')
            secDistList = self.secDistances(CSNodes)
            for node in secDistList:
                textString += ('{0:15E}'.format(node[0]) +
                               '    ' + '{0:15E}'.format(node[1]) + '\n')
            textString += ('// Top and Toe point IDs in the profile list\n')
            topNodeSeq = CSNodes.index(topNode) + 1
            toeNodeSeq = CSNodes.index(toeNode) + 1
            line = 'TOPTOE_ID    '
            line += (str(topNodeSeq) + '   ')
            line += (str(toeNodeSeq) + '\n')
            textString += line
            textString += '// Ground water elevation (meter); use -999 for '
            textString += 'non-cohesive bank\n'
            line = 'GW_ELEV    '
            line += '{0:12E}'.format(bankItem.bankData.layerItems[0].grdWatLvl)
            line += '\n'
            textString += line
            textString += (
                '// Number of bank Layers (order: from top to bottom)\n')
            line = 'N_LAYER  ' + str(len(bankItem.bankData.layerItems)) + '\n'
            textString += line
            textString += ('// Properties for each bank layer ' +
                           '(from top to bottom):\n')
            textString += ('// Bottom_Elev(m),Porosity,Saturated_Weight(N/m3)' +
                           ',Tau_cri(Pa),Erodibility(m/s),Fric_ang/Repose(deg' +
                           '),Phib(deg),C_prim(Pa)\n')
            for i in range(0, len(bankItem.bankData.layerItems)):
                layer = bankItem.bankData.layerItems[i]
                line = '    '
                line += ('{0:12E}'.format(layer.minElev) + '    ')
                line += ('{0:12E}'.format(layer.porosity) + '    ')
                line += ('{0:12E}'.format(layer.ssw) + '    ')
                line += ('{0:12E}'.format(layer.tau) + '    ')
                line += ('{0:12E}'.format(layer.erodibility) + '    ')
                line += ('{0:12E}'.format(layer.phi) + '    ')
                line += ('{0:12E}'.format(layer.phib) + '    ')
                line += ('{0:12E}'.format(layer.coh))
                line += '\n'
                textString += line
            textString += '// Composition for each layer (sediment classes are '
            textString += 'defined by SRH2D input file)\n'
            for i in range(0, len(bankItem.bankData.layerItems)):
                layer = bankItem.bankData.layerItems[i]
                line = '    '
                for j in range(0, len(layer.gradList)):
                    line += ('{0:12E}'.format(layer.gradList[j][2]) + '    ')
                line = line[:-4] + '\n'
                textString += line

        bankItem.textString = textString
        viewer = self.dlg.secPropertyViewer
        viewer.clear()
        viewer.append(textString)


class bankCSListItem(QListWidgetItem):
    def __init__(self, parent, mNodeLayer, bankNodes):
        super(bankCSListItem, self).__init__(parent, 0)
        self.mNodeLayer = mNodeLayer
        self.bankNodes = bankNodes
        self.pairNum = 0
        self.bankData = ''
        self.Type = 'Move'

    def selectByNode(self):
        nodeLayerId = self.mNodeLayer.id()
        layer = QgsMapLayerRegistry.instance().mapLayer(nodeLayerId)
        node_ids = list()
        for node in self.bankNodes:
            querryString = "id=" + str(node)
            expr = QgsExpression(querryString)
            feats = layer.getFeatures(QgsFeatureRequest(expr))
            ids = [i.id() for i in feats]
            node_ids += ids

        layer.setSelectedFeatures(node_ids)

    def genText(self):
        if self.bankData:
            self.textString = ''
