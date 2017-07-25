# -*- coding: big5 -*-

import os
from PyQt4 import QtGui, uic
from PyQt4.QtCore import QVariant, QFileInfo
from PyQt4.QtCore import QSettings, qVersion, QTranslator, QCoreApplication
from qgis.core import QgsProject, QgsFields, QgsField, QgsVectorFileWriter
from qgis.core import QgsCoordinateReferenceSystem, QGis, QgsFeature
from qgis.core import QgsGeometry, QgsMapLayerRegistry, QgsVectorLayer
from qgis.gui import QgsGenericProjectionSelector
from commonDialog import fileBrowser, folderBrowser
from math import fabs


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '2dmMeshViewer.ui'))


class mesh2DViewDiag(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(mesh2DViewDiag, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)


meshType = {'E3T': 3, 'E4Q': 4, 'E6T': 6, 'E8Q': 8, 'E9Q': 9}


class mesh2DView:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'meshBuilder_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.dlg = mesh2DViewDiag()

        caption1 = u'請選擇一個 mesh2D 檔案(.2dm)'
        self.dlg.mshFileSelectBtn.pressed.connect(
            lambda: fileBrowser(self.dlg, caption1, '', self.dlg.meshFileEdit,
                                '(*.2dm)'))
        caption2 = u'請選擇建立 shp 檔案的資料夾'
        self.dlg.folderSelectBtn.pressed.connect(
            lambda: folderBrowser(self.dlg, caption2, '',
                                  self.dlg.folderLineEdit))
        self.dlg.geoReferenceBtn.clicked.connect(self.selectCrs)

    def run(self):
        result = self.dlg.exec_()
        if result:
            self.read2dm()
            return result

    def selectCrs(self):
        crsDiag = QgsGenericProjectionSelector()
        crsDiag.exec_()
        crsId = crsDiag.selectedCrsId()
        crsType = QgsCoordinateReferenceSystem.InternalCrsId
        self.crs = QgsCoordinateReferenceSystem(crsId, crsType)

    def read2dm(self):
        try:
            crs = self.crs
        except(AttributeError):
            crs = QgsCoordinateReferenceSystem(
                3826, QgsCoordinateReferenceSystem.EpsgCrsId)
        meshFile = self.dlg.meshFileEdit.text()
        f = open(meshFile, 'r')

        data = f.readlines()
        NodeDict = dict()
        Regions = list()
        NodeStrings = list()
        oneString = list()
        for line in data:
            line = line.split()
            if line[0] == 'ND':
                NodeDict.update(
                    {int(line[1]): (float(line[2]), float(line[3]),
                                    float(line[4]))})
            elif line[0] in meshType.keys():
                Regions.append(line[-1])
            elif line[0] == 'NS':
                for i in range(1, len(line)):
                    oneString.append(fabs(int(line[i])))
                if int(line[-1]) < 0:
                    NodeStrings.append(oneString)
                    oneString = list()

        Regions = list(set(Regions))
        Regions.sort()

        group = QgsProject.instance().layerTreeRoot().addGroup(
            os.path.basename(meshFile))

        regionWriters = list()
        fields = QgsFields()
        fields.append(QgsField("id", QVariant.Int))
        layerList = list()
        for i in range(0, len(Regions)):
            layerName = 'Material' + Regions[i]
            path = os.path.join(self.dlg.folderLineEdit.text(),
                                layerName + '.shp')
            self.iface.messageBar().pushMessage(path)
            regionWriters.append(
                QgsVectorFileWriter(path, 'UTF-8', fields, QGis.WKBPolygon, crs,
                                    'ESRI Shapefile'))
            layerList.append(path)
        for line in data:
            line = line.split()
            if line[0] in meshType.keys():
                n = meshType[line[0]]
                geoString = 'POLYGON (('
                for k in range(2, 2+n):
                    Coor = NodeDict[int(line[k])]
                    geoString += (str(Coor[0]) + ' ' + str(Coor[1]) + ', ')
                Coor = NodeDict[int(line[2])]
                geoString += (str(Coor[0]) + ' ' + str(Coor[1]))
                geoString += '))'
                writer = regionWriters[int(line[-1])-1]

                feature = QgsFeature()
                feature.setGeometry(QgsGeometry().fromWkt(geoString))
                feature.setAttributes([int(line[1])])
                writer.addFeature(feature)

                if writer.hasError() != QgsVectorFileWriter.NoError:
                    self.iface.messageBar().pushMessage(
                        "Error when creating shapefile: ",
                        writer.errorMessage())

        for writer in regionWriters:
            del writer

        counter = 1
        for lineString in NodeStrings:
            path = os.path.join(self.dlg.folderLineEdit.text(),
                                'NodeString' + str(counter) + '.shp')
            writer = QgsVectorFileWriter(path, 'UTF-8', fields,
                                         QGis.WKBLineString, crs,
                                         'ESRI Shapefile')
            layerList.append(path)
            geoString = 'LINESTRING ('
            for i in range(0, len(lineString)):
                nodeCoor = NodeDict[lineString[i]]
                geoString += (str(nodeCoor[0]) + " " + str(nodeCoor[1]) + ", ")
            geoString = geoString[:-2] + ')'

            feature = QgsFeature()
            feature.setGeometry(QgsGeometry().fromWkt(geoString))
            feature.setAttributes([counter])
            writer.addFeature(feature)
            del writer
            counter += 1

        for i in range(0, len(layerList)):
            layer = QgsVectorLayer(
                layerList[i], QFileInfo(layerList[i]).baseName(), 'ogr')
            QgsMapLayerRegistry.instance().addMapLayer(layer, False)
            group.addLayer(layer)
            layer.reload()
