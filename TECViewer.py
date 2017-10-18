# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TECView
                                 A QGIS plugin
 Reading the results of SRH2D TEC output
                              -------------------
        begin                : 2017-10-17
        git sha              : $Format:%H$
        copyright            : (C) 2017 by ManySplendid co.
        email                : yengtinglin@manysplendid.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QListWidgetItem
# Initialize Qt resources from file resources.py
import resources
import processing
import subprocess
import re
# Import the code for the dialog
from TECViewer_dialog import TECViewDialog
from math import ceil
from qgis.core import QgsVectorFileWriter, QgsVectorLayer, QgsFeature
from qgis.core import QgsGeometry, QGis, QgsFields, QgsField, QgsRasterLayer
from qgis.core import QgsCoordinateReferenceSystem, QgsMapLayerRegistry
from qgis.core import QgsProject
from qgis.gui import QgsGenericProjectionSelector
from PyQt4.QtCore import QVariant, QFileInfo
from osgeo import osr, gdal
from gdalconst import GA_Update
from itertools import izip as zip, count
import os


class TECView:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'TECView_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&SRH2D_TECViewer')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'TECView')
        self.toolbar.setObjectName(u'TECView')
        self.dlg = TECViewDialog()

        self.dlg.fileListWidget.clear()
        self.dlg.attributeList.clear()

        # - Button Connections  - #
        self.dlg.selectProjFolder.clicked.connect(self.selectProjFolder)
        self.dlg.geoRefBtn.clicked.connect(self.selectCrs)
        self.dlg.addFileBtn.clicked.connect(self.selectTECFile)
        self.dlg.deleteFileBtn.clicked.connect(self.removeTECfile)
        self.dlg.fileListWidget.itemSelectionChanged.connect(self.showAttr)
        self.dlg.cancelLoadBtn.clicked.connect(lambda: self.dlg.done(0))
        self.dlg.attributeList.clicked.connect(self.selectToShow)
        self.dlg.loadTECBtn.clicked.connect(self.loadTECfiles)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('TECView', message)

    def add_action(self, icon_path, text, callback, enabled_flag=True,
                   add_to_menu=True, add_to_toolbar=True, status_tip=None,
                   whats_this=None, parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/TECView/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'SRH2D Post-Processing TEC File Viewer and analyser.'
                         ),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&SRH2D_TECViewer'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

    def selectProjFolder(self):
        try:
            presetFolder = self.dlg.settings['last_proj']
        except(KeyError):
            presetFolder = ''
        caption = 'Please choose a project folder'
        folderName = QFileDialog.getExistingDirectory(self.dlg, caption,
                                                      presetFolder)
        self.dlg.projFolderEdit.setText(folderName)

    def selectCrs(self):
        crsDiag = QgsGenericProjectionSelector()
        crsDiag.exec_()
        crsId = crsDiag.selectedCrsId()
        crsType = QgsCoordinateReferenceSystem.InternalCrsId
        self.systemCRS = QgsCoordinateReferenceSystem(crsId, crsType)

    def selectTECFile(self):
        Caption = 'Please select a _TEC_.dat file or multiple files'
        projFolder = self.dlg.projFolderEdit.text()
        filePathes = QFileDialog.getOpenFileNames(
            self.dlg, Caption, os.path.join(projFolder, 'sim'), "*.dat")
        for path in filePathes:
            fileWidget = TECfile(self.dlg.fileListWidget, 0, path)
            self.dlg.fileListWidget.addItem(fileWidget)

    def removeTECfile(self):
        selectedTEC = self.dlg.fileListWidget.currentItem()
        c_row = self.dlg.fileListWidget.row(selectedTEC)
        self.dlg.fileListWidget.takeItem(c_row)

    def showAttr(self):
        self.dlg.attributeList.clear()
        current = self.dlg.fileListWidget.currentItem()
        attributes = current.attributes
        for attr in attributes:
            item = QListWidgetItem(attr[0], self.dlg.attributeList)
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            if attr[1] == 0:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)
            self.dlg.attributeList.addItem(item)

    def changeAttrToOutput(self, TECitem, attr):
        idx = [r for r, j in zip(count(), TECitem.attributes) if attr in j][0]
        TECitem.attributes[idx][1] = 1

    def changeAttrToCancel(self, TECitem, attr):
        idx = [r for r, j in zip(count(), TECitem.attributes) if attr in j][0]
        TECitem.attributes[idx][1] = 0

    def selectToShow(self):
        attrList = self.dlg.attributeList
        for i in range(0, attrList.count()):
            attrItem = attrList.item(i)
            attrName = attrItem.text()
            if attrItem.checkState() == Qt.Checked:
                if self.dlg.chageAllBtn.isChecked():
                    for t in range(0, self.dlg.fileListWidget.count()):
                        TECitem = self.dlg.fileListWidget.item(t)
                        self.changeAttrToOutput(TECitem, attrName)
                else:
                    TECitem = self.dlg.fileListWidget.currentItem()
                    self.changeAttrToOutput(TECitem, attrName)
            else:
                if self.dlg.chageAllBtn.isChecked():
                    for t in range(0, self.dlg.fileListWidget.count()):
                        TECitem = self.dlg.fileListWidget.item(t)
                        self.changeAttrToCancel(TECitem, attrName)
                else:
                    TECitem = self.dlg.fileListWidget.currentItem()
                    self.changeAttrToCancel(TECitem, attrName)

    def writeSettings(self):
        plugin_fol = os.path.dirname(__file__)
        f = open(os.path.join(plugin_fol, '_settings_'), 'w')
        proj_Fol = self.dlg.projFolderEdit.text()
        f.write('last_proj = ' + proj_Fol)
        f.close()

    def loadTECfiles(self):
        projFolder = self.dlg.projFolderEdit.text()
        outFolder = os.path.join(projFolder, 'TECView')
        if not os.path.isdir(outFolder):
            os.system('mkdir ' + outFolder)
        for i in range(0, self.dlg.fileListWidget.count()):
            TECitem = self.dlg.fileListWidget.item(i)
            self.iface.messageBar().pushMessage(
                'generating ' + TECitem.fileName)
            TECitem.outDir = outFolder
            TECitem.iface = self.iface
            TECitem.export()
        self.writeSettings()
        self.dlg.done(1)


class TECfile(QListWidgetItem):
    def __init__(self, parent, widgetType, filePath):
        super(TECfile, self).__init__(parent, widgetType)
        self.filePath = filePath
        self.fileName = os.path.basename(filePath)
        self.headerLinesCount = 0
        self.TECTile = ''
        self.variables = list()
        self.composition = dict()
        self.variableType = list()
        self.readTEC(filePath)
        self.outDir = ''
        refId = QgsCoordinateReferenceSystem.PostgisCrsId
        crs = QgsCoordinateReferenceSystem(3826, refId)
        self.crs = crs
        self.iface = ''

        self.setText(os.path.basename(filePath))

    def readTEC(self, filePath):
        f = open(filePath)
        dat = f.readlines()
        self.getVariables(dat)
        self.dat = dat

    def loadTEC(self):
        self.readVariables(self.dat)

        for i in range(0, len(self.variables[3]['Water_Elev_m'])):
            if float(self.variables[3]['Water_Elev_m'][i]) == -999.0:
                self.variables[3][
                    'Water_Elev_m'][i] = self.variables[2]['Bed_Elev_meter'][i]
        self.makeMeshLayer()
        self.makeSieve()
        self.genNodeLayer()

    def export(self):
        self.outDir = os.path.join(self.outDir,
                                   self.fileName.replace('.dat', ''))
        if os.path.isdir(self.outDir):
            subprocess.call(['cmd', '/c', 'RD', '/S', '/Q', self.outDir])
            subprocess.call(['cmd', '/c', 'mkdir', self.outDir])
            subprocess.call(['cmd', '/c', 'mkdir',
                             os.path.join(self.outDir, 'supplements')])
        else:
            subprocess.call(['cmd', '/c', 'mkdir', self.outDir])
            subprocess.call(['cmd', '/c', 'mkdir',
                             os.path.join(self.outDir, 'supplements')])
        self.loadTEC()
        group = QgsProject.instance().layerTreeRoot().addGroup(self.fileName)
        for attr in self.attributes:
            if attr[1] == 1:
                self.makeContentLayers(attr[0])
                if len(attr[0]) > 10:
                    rasterName = attr[0][0:10]
                else:
                    rasterName = attr[0]
                rasterPath = os.path.join(self.outDir, rasterName + '.tif')
                baseName = QFileInfo(rasterPath).baseName()
                rasterLayer = QgsRasterLayer(rasterPath, baseName)
                QgsMapLayerRegistry.instance().addMapLayer(rasterLayer, False)
                group.addLayer(rasterLayer)

    def attributeList(self):
        attributes = self.attributes
        _attrs = list()
        for i in range(2, len(attributes)):
            _attrs.append([attributes[i], 0])
        self.attributes = _attrs

    def getVariables(self, dat):
        def readDat(dat, title, _variable, ZONE, DT):
            mode = 0
            lineCount = 0
            for line in dat:
                if line.startswith(' TITLE'):
                    mode = 0
                elif line.startswith(' VARIABLES'):
                    mode = 1
                elif line.startswith(' ZONE'):
                    mode = 2
                elif line.startswith(' DT'):
                    mode = 3
                elif line.endswith(')\n'):
                    mode = 4

                if mode == 0:
                    title.append(line)
                elif mode == 1:
                    _variables.append(line)
                elif mode == 2:
                    ZONE.append(line)
                elif mode == 3 or mode == 4:
                    DT.append(line)
                    if line.endswith(')\n'):
                        mode = 5
                else:
                    return (title, _variable, ZONE, DT, lineCount)
                lineCount += 1

        title = list()
        _variables = list()
        ZONE = list()
        DT = list()

        title, _variables, ZONE, DT, lineCount = readDat(dat, title, _variables,
                                                         ZONE, DT)

        self.headerLinesCount = lineCount

        titleString = ''
        for line in title:
            titleString += line

        titleString.replace('\n', '')
        titleString.replace('"', '')
        titleString = re.split('=', titleString)
        self.TECTitle = titleString[1].replace('\n', '').strip()

        variableString = ''
        for line in _variables:
            variableString += line
        variableString.replace('\n', '')
        self.variables = re.findall(r'\S+', variableString)
        self.attributes = re.findall(r'\S+', variableString)
        self.variables.pop(0)
        self.attributes.pop(0)
        self.variables[0] = self.variables[0].replace('=', '')
        self.attributes[0] = self.attributes[0].replace('=', '')
        self.attributeList()

        zoneString = ''
        for line in ZONE:
            zoneString += line
        zoneSplit = re.split(',', zoneString)
        zoneSplit[0] = zoneSplit[0].replace(' ZONE ', '')
        for unit in zoneSplit:
            self.composition.update({unit.split('=')[0]:
                                     unit.split('=')[1].strip()})

        DTstring = ''
        for line in DT:
            DTstring += line
        DTstring = DTstring.replace(' DT=(', '')
        DTstring = DTstring.replace(' \n', '')
        DTstring = DTstring.replace(')\n', '')
        vtype = re.split('\s', DTstring.strip())
        self.variableType = vtype

    def readVariables(self, dat):
        lineCounter = int(ceil(float(self.composition['N'])/5))
        variables = self.variables
        totalVaraibles = len(variables)

        readCounter = 0
        variableCounter = 0
        data = list()
        mesh = list()
        for i in range(self.headerLinesCount, len(dat)):
            row = re.findall(r'\S+', dat[i])
            for number in row:
                data.append(number)
            readCounter += 1

            if ((readCounter == lineCounter) and
                    (variableCounter < totalVaraibles)):
                variables[variableCounter] = {str(variables[variableCounter]):
                                              data}
                variableCounter += 1
                data = list()
                readCounter = 0
            elif variableCounter >= totalVaraibles:
                polygon = list()
                for node in dat[i].split():
                    polygon.append(int(node))
                mesh.append(polygon)
        self.mesh = mesh

    def makeMeshLayer(self):
        mesh = self.mesh
        Xkey = self.variables[0].keys()[0]
        X = self.variables[0][Xkey]
        self.Xmax = max(X)
        self.Xmin = min(X)
        Ykey = self.variables[1].keys()[0]
        Y = self.variables[1][Ykey]
        self.Ymax = max(Y)
        self.Ymin = min(Y)
        c_folder = self.outDir
        crs = self.crs
        path = os.path.join(c_folder, 'mesh.shp')
        self.layerPath = path
        fields = QgsFields()
        fields.append(QgsField("id", QVariant.Int))
        fields.append(QgsField("val", QVariant.Int))

        writer = QgsVectorFileWriter(path, 'utf-8', fields, QGis.WKBPolygon,
                                     crs, "ESRI Shapefile")
        feat_id = 1
        for polygon in mesh:
            feature = QgsFeature()
            geoString = 'POLYGON (('
            if polygon[-1] == polygon[-2]:
                polygon[-1] = polygon[0]
            else:
                polygon.append(polygon[0])
            for node in polygon:
                geoString += (X[node-1] + " " + Y[node-1] + ",")
            geoString = geoString[:-1] + "))"
            feature.setGeometry(QgsGeometry.fromWkt(geoString))
            feature.setAttributes([feat_id, 1])
            writer.addFeature(feature)
            feat_id += 1
        layer = QgsVectorLayer(path, QFileInfo(path).baseName(), 'ogr')
        self.meshLayer = layer

    def makeSieve(self):
        layer = self.meshLayer
        sievePath = os.path.join(self.outDir, 'sieve.tif')
        xmin = float(self.Xmin)
        xmax = float(self.Xmax)
        ymin = float(self.Ymin)
        ymax = float(self.Ymax)
        processing.runalg('gdalogr:rasterize',
                          {"INPUT": layer,
                           "FIELD": "val",
                           "DIMENSIONS": 1,
                           "WIDTH": 1.0,
                           "HEIGHT": 1.0,
                           "RAST_EXT": "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                           "TFW": 1,
                           "RTYPE": 4,
                           "NO_DATA": -1,
                           "COMPRESS": 0,
                           "JPEGCOMPRESSION": 1,
                           "ZLEVEL": 1,
                           "PREDICTOR": 1,
                           "TILED": False,
                           "BIGTIFF": 0,
                           "EXTRA": '',
                           "OUTPUT": sievePath})
        crs = self.crs

        dataset = gdal.Open(sievePath, GA_Update)
        # band = dataset.GetRasterBand(1)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3826)
        dataset.SetProjection(srs.ExportToWkt())
        # dataset = None

        sieveLayer = QgsRasterLayer(sievePath, QFileInfo(sievePath).baseName())
        self.sieveLayer = sieveLayer
        self.sieveLayer.setCrs(crs)

    def genNodeLayer(self):
        crs = self.crs
        baseName = os.path.splitext(self.fileName)[0]
        path = os.path.join(self.outDir, baseName + '.shp')

        fields = QgsFields()
        for i in range(2, len(self.variables)):
            fieldName = self.variables[i].keys()[0]
            if self.variableType[i] == 'DOUBLE':
                fields.append(QgsField(fieldName, QVariant.Double))
            elif self.variableType[i] == 'INT':
                fields.append(QgsField(fieldName, QVariant.Int))

        writer = QgsVectorFileWriter(path, 'utf-8', fields, QGis.WKBPoint,
                                     crs, "ESRI Shapefile")

        Xkey = self.variables[0].keys()[0]
        X = self.variables[0][Xkey]
        Ykey = self.variables[1].keys()[0]
        Y = self.variables[1][Ykey]

        for i in range(0, len(X)):
            geoString = 'POINT (' + str(X[i]) + ' ' + str(Y[i]) + ')'
            attr = list()
            #
            for j in range(2, len(self.variables)):
                fieldName = self.variables[j].keys()[0]
                attr.append(self.variables[j][fieldName][i])
            #
            point = QgsFeature()
            point.setGeometry(QgsGeometry.fromWkt(geoString))
            point.setAttributes(attr)
            writer.addFeature(point)

        del writer
        nodeLayer = QgsVectorLayer(path, QFileInfo(path).baseName(), 'ogr')
        self.nodeLayer = nodeLayer

    def makeContentLayers(self, fieldKey):
        xmin = float(self.Xmin)
        xmax = float(self.Xmax)
        ymin = float(self.Ymin)
        ymax = float(self.Ymax)
        c_folder = self.outDir

        if len(fieldKey) > 10:
            fieldName = fieldKey[0:10]
        else:
            fieldName = fieldKey

        rasterName = fieldName
        processing.runalg('grass7:v.surf.rst',
                          {'input': self.nodeLayer,
                           'where': '',
                           'mask': self.sieveLayer,
                           'zcolumn': fieldName,
                           'tension': 40.0,
                           'segmax': 40.0,
                           'npmin': 300.0,
                           'dmin': 1.0e-3,
                           'dmax': 2.50,
                           'zscale': 1.0,
                           'theta': 0.0,
                           'scalex': 0.0,
                           '-t': False,
                           '-d': False,
                           'GRASS_REGION_PARAMETER':
                           "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                           'GRASS_REGION_CELLSIZE_PARAMETER': 5.0,
                           'GRASS_SNAP_TOLERANCE_PARAMETER': -1.0,
                           'GRASS_MIN_AREA_PARAMETER': 1.0e-4,
                           'elevation': os.path.join(c_folder, rasterName),
                           'slope': os.path.join(
                               os.path.join(c_folder, 'supplements'),
                               rasterName + '-slope'),
                           'aspect': os.path.join(
                               os.path.join(c_folder, 'supplements'),
                               rasterName + '-aspect'),
                           'pcurvature': os.path.join(
                               os.path.join(c_folder, 'supplements'),
                               rasterName + '-pcurv'),
                           'tcurvature': os.path.join(
                               os.path.join(c_folder, 'supplements'),
                               rasterName + '-tcurv'),
                           'mcurvature': os.path.join(
                               os.path.join(c_folder, 'supplements'),
                               rasterName + '-mcurv')
                           })
