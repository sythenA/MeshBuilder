import os
import re
import os.path
from PyQt4 import uic
from PyQt4.QtGui import QDialog
from PyQt4.QtCore import QVariant
from qgis.core import QgsFeature, QgsFields, QgsField, QgsVectorFileWriter, QGis
from qgis.core import QgsGeometry
import subprocess


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'loadLayerProgress.ui'))


class loadProgDiag(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(loadProgDiag, self).__init__(parent)
        self.setupUi(self)


class loadLayerPop:
    def __init__(self, iface, mesh, projFolder, crs):
        self.iface = iface
        self.mesh = mesh
        self.projFolder = projFolder
        self.crs = crs
        self.dlg = loadProgDiag(parent=iface.mainWindow())

    def run(self):
        self.loadMeshNodes()
        result = self.dlg.exec_()
        if result:
            return [self.nodePath, self.boundaryPath]

    def checkFolder(self):
        folderPath = os.path.join(self.projFolder, 'MeshShp', 'bank')
        if not os.path.isdir(folderPath):
            subprocess.Popen(['mkdir', folderPath])

    def breakNS(self, nodeString):
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

        counter = 0
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
            self.dlg.progressBar.setValue(int(counter/len(dat)))
            counter += 1

        del NodeWriter

        boundaries = self.breakNS(NSlist)
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
