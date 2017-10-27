import os
import re
from math import sqrt
from operator import itemgetter
from PyQt4 import uic
from PyQt4.QtGui import QDialog


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
        if nodeString[i] >= 0:
            boundary.append(nodeString[i])
        else:
            boundary.append(-nodeString[i])
            boundaries.append(boundary)
            boundary = list()
    return boundaries


class bankCross:
    def __init__(self, meshPath, toe, top):
        self.readMesh(meshPath, toe, top)
        self.setEndNodes(2)

    def readMesh(self, meshPath, toe, top):
        f = open(meshPath, 'r')
        dat = f.readlines()
        id_list = list()
        nodes = dict()
        NodeString = list()
        mesh_list = list()

        for line in dat:
            lineSeg = re.split('\s+', line.strip())
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
        for i in range(0, len(self.Tops)):
            tops = list()
            for j in range(0, len(self.Tops[i]), jump):
                tops.append(self.Tops[i][j])
            if j + jump > len(self.Tops[i]):
                tops.append(self.Tops[i][-1])
            Top_Ids.append(tops)
        for i in range(0, len(self.Toes)):
            toes = list()
            for j in range(0, len(self.Toes[i]), jump):
                toes.append(self.Toes[i][j])
            if j + jump > len(self.Toes[i]):
                tops.append(self.Toes[i][-1])
            Toe_Ids.append(toes)

        pair = zip(Toe_Ids, Top_Ids)
        for i in range(0, len(pair)):
            pair[i] = zip(pair[i][0], pair[i][1])

        self.twoEnds = pair

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

        return dist_list[0:10]

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
                if i > 0:
                    return element[i-1]
                else:
                    return element[-2]
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
                    nextOnToe = toe[idx+1]

                    for element in self.elements:
                        if bank[0] in element and nextOnToe in element:
                            tarNode = self.nodeInElement(
                                bank[0], nextOnToe, element)
                            if tarNode and tarNode not in banList:
                                bank.insert(0, tarNode)
                except:
                    pass
            for top in self.Tops:
                try:
                    idx = top.index(bank[-1])
                    nextOnTop = top[idx+1]

                    for element in self.elements:
                        if bank[-1] in element and nextOnTop in element:
                            tarNode = self.nodeInElement(
                                bank[-1], nextOnTop, element)
                            if tarNode and tarNode not in banList:
                                bank.append(tarNode)
                except:
                    pass


class bankCrossSecSetting:
    def __init__(self, iface, mesh, Toes, Tops):
        self.iface = iface
        self.mesh = mesh
        self.dlg = bankCrossSecDiag()

    def run(self):
        self.dlg.show()

    def loadMeshNodes(self):
        f = open(self.mesh, 'r')
        dat = f.readlines()
        f.close()




"""
bank = bankCross('D:/test/proj23/proj23.2dm', [3, 5], [4, 6])
bank.findBetween()
bank.findOutSide()
print bank.CS"""
