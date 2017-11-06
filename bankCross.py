import os
import re
from math import sqrt
from operator import itemgetter
from qgis.core import QgsVectorLayer, QgsMapLayerRegistry, QgsVectorFileWriter
from qgis.core import QgsFields, QgsField, QgsGeometry, QgsFeature, QGis
from qgis.core import QgsFeatureRequest, QgsExpression
from PyQt4 import uic
from PyQt4.QtGui import QDialog, QListWidgetItem
from PyQt4.QtCore import QVariant, Qt
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
        for i in range(0, len(self.Tops)):
            tops = list()
            for j in range(0, len(self.Tops[i]), jump):
                tops.append(self.Tops[i][j])

            if self.Tops[i][-1] not in tops:
                tops.append(self.Tops[i][-1])
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
    def __init__(self, iface, projFolder, nodePath, boundaryPath, bankCS):
        self.iface = iface
        self.projFolder = projFolder
        self.dlg = bankCrossSecDiag(parent=iface.mainWindow())
        self.nodePath = nodePath
        self.boundaryPath = boundaryPath
        self.loadLayer()
        self.bankCS = bankCS
        self.loadCrossSecs()

        self.dlg.sectionList.itemClicked.connect(self.showSec)

    def run(self):
        self.dlg.exec_()

    def checkFolder(self):
        folderPath = os.path.join(self.projFolder, 'MeshShp', 'bank')
        if not os.path.isdir(folderPath):
            subprocess.Popen(['mkdir', folderPath])

    def loadCrossSecs(self):
        bankCS = self.bankCS

        for sec in bankCS.CS:
            bankSecItem = bankCSListItem(self.dlg.sectionList, self.mNodeLayer,
                                         sec)
            idx = bankCS.CS.index(sec)
            bankSecItem.setText('bank Cross-Section ' + str(idx+1).zfill(2))
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

    def showSec(self):
        self.dlg.setWindowModality(Qt.NonModal)
        bankItem = self.dlg.sectionList.currentItem()
        bankItem.selectByNode()


class bankCSListItem(QListWidgetItem):
    def __init__(self, parent, mNodeLayer, bankNodes):
        super(bankCSListItem, self).__init__(parent, 0)
        self.mNodeLayer = mNodeLayer
        self.bankNodes = bankNodes

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
