# -*- coding: big5 -*-
"""
/***************************************************************************
 meshBuilder
                                 A QGIS plugin
 Build mesh for SRH2D
                              -------------------
        begin                : 2017-05-02
        git sha              : $Format:%H$
        copyright            : (C) 2017 by ManySplendid.co
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
from PyQt4.QtCore import QFileInfo, QPyNullVariant
from PyQt4.QtCore import QProcess, QProcessEnvironment, QVariant
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QListWidgetItem
from PyQt4.QtGui import QMessageBox, QColor
from qgis.core import QgsVectorLayer, QgsMapLayerRegistry, QgsVectorFileWriter
from qgis.core import QgsGeometry, QgsFeature, QGis, QgsFields, QgsField
from qgis.core import QgsCoordinateReferenceSystem, QgsProject, QgsPoint
from PyQt4.QtGui import QTableWidgetItem, QComboBox
from qgis.utils import iface
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from meshBuilder_dialog import meshBuilderDialog
import shepred
import os.path
import newPointLayer
import lineFrame
from innerLayers import innerLayersExport
from exportToGeo import genGeo
from shutil import rmtree
import os


class meshBuilder:
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
            'meshBuilder_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.dlg = meshBuilderDialog()
        self.shepred = shepred.shepred(iface)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Mesh Builder')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'meshBuilder')
        self.toolbar.setObjectName(u'meshBuilder')

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
        return QCoreApplication.translate('meshBuilder', message)

    def add_action(self,
                   icon_path,
                   text,
                   callback,
                   enabled_flag=True,
                   add_to_menu=True,
                   add_to_toolbar=True,
                   status_tip=None,
                   whats_this=None,
                   parent=None):
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
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/meshBuilder/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Build Mesh For SRH2D'),
            callback=self.run,
            parent=self.iface.mainWindow())
        shepredTr = QCoreApplication.translate('shepred UI', 'shepred UI')
        ShepredAction = QAction(QIcon(icon_path), shepredTr,
                                self.iface.mainWindow())
        ShepredAction.triggered.connect(lambda: self.shepred.run())
        ShepredAction.setEnabled(True)
        self.iface.addPluginToMenu(self.menu, ShepredAction)
        self.actions.append(ShepredAction)
        self.toolbar = self.iface.addToolBar(u'shepred UI')
        self.toolbar.setObjectName(u'shepredUI')

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Mesh Builder'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def folderBrowser(self, caption="", Dir=os.getcwd(),
                      lineEdit=""):
        folderName = QFileDialog.getExistingDirectory(self.dlg,
                                                      caption)
        if lineEdit:
            if folderName:
                lineEdit.setText(folderName)

    def fileBrowser(self, Caption, presetFolder, lineEdit="",
                    presetType=".shp"):
        if not presetFolder:
            presetFolder = self.projFolder

        fileName = QFileDialog.getOpenFileName(self.dlg, Caption,
                                               presetFolder, "*" + presetType)
        if lineEdit:
            if fileName:
                lineEdit.setText(fileName)

    def saveFileBrowser(self, Caption, presetFolder, lineEdit="",
                        presetType=".shp"):
        if not presetFolder:
            presetFolder = self.projFolder

        fileName = QFileDialog.getSaveFileName(self.dlg, Caption,
                                               presetFolder, "*" + presetType)
        if fileName and lineEdit:
            lineEdit.setText(fileName)

    def cleanProjFolder(self, projFolder):
        projFolder.replace("\\", "/")
        files = os.listdir(projFolder)
        for name in files:
            if os.path.isfile(projFolder + "\\" + name):
                os.remove(projFolder + "\\" + name)

        if os.path.isdir(projFolder + '\\MainLayers'):
            files = rmtree(projFolder + '\\MainLayers')
            os.mkdir(projFolder + '\\MainLayers')
        else:
            os.mkdir(projFolder + '\\MainLayers')

        if os.path.isdir(projFolder + '\\InnerLayers'):
            files = rmtree(projFolder + '\\InnerLayers')
            os.mkdir(projFolder + '\\InnerLayers')
        else:
            os.mkdir(projFolder + '\\InnerLayers')

    def step1_1(self):

        projFolder = str(self.dlg.lineEdit.text())
        self.projFolder = projFolder
        self.cleanProjFolder(projFolder)

        layers = self.iface.legendInterface().layers()

        MainName = self.dlg.comboBox.currentText()
        if MainName:
            for layer in layers:
                if layer.name() == MainName:
                    mainLayerSelected = layer
            self.systemCRS = mainLayerSelected.dataProvider().crs()

            newMainLayer = newPointLayer.copyMainLayer(mainLayerSelected,
                                                       projFolder)
            if newMainLayer:
                self.mainLayer = newMainLayer
            else:
                self.mainLayer = mainLayerSelected

            self.mainLayer.setCrs(self.systemCRS)
            source = self.mainLayer.dataProvider().dataSourceUri().split('|')[0]
            #
            #  Load the assinged shape file layer into qgis, and show on the
            #  canvas.
            #
            iface.addVectorLayer(source, QFileInfo(source).baseName(), 'ogr')
        else:
            source = ""

        innerLayersChecked = list()
        for i in range(0, self.dlg.listWidget.count()):
            item = self.dlg.listWidget.item(i)
            if item.checkState() == Qt.Checked:
                innerLayersChecked.append(item.text())
        innerLayersList = list()
        for layer in layers:
            if layer.name() in innerLayersChecked:
                innerLayersList.append(layer)

        if MainName:
            innerLayers = innerLayersExport(projFolder, newMainLayer)
            innerLayers.innerLayers = innerLayersList
            innerLayers.copyLayers()
        else:
            if innerLayersList:
                message = u'主圖層未指定'
                detail = u'不能在未指定主圖層的情況下指定內邊界圖層'
                self.criticalBox(message, detail)

        self.dlg.tabWidget.setTabEnabled(1, True)
        self.dlg.tabWidget.setCurrentIndex(1)
        self.step2(source)

    def step1(self):
        def chkSwitch():
            if not self.dlg.lineEdit.text():
                message = u'未指定專案資料夾'
                detail = u'進行下一步之前必需設定專案資料夾\n請先設定專案資料夾\
再進行下一步'
                self.criticalBox(message, detail)
            elif not os.path.isdir(self.dlg.lineEdit.text()):
                message = u'指定了錯的專案資料夾'
                detail = u'您指定的專案資料夾不是可用的路徑\n請重新指定專案資料\
夾'
                self.criticalBox(message, detail)
            else:
                self.step1_1()

        layers = self.iface.legendInterface().layers()
        self.dlg.comboBox.clear()

        layerList = list()
        innerLayerList = list()
        for layer in layers:
            innerLayerList.append(layer.name())
            if layer.geometryType() > 1:
                layerList.append(layer.name())
        self.dlg.comboBox.addItems(layerList)

        self.dlg.listWidget.clear()

        for name in innerLayerList:
            item = QListWidgetItem(name, self.dlg.listWidget)
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            item.setCheckState(Qt.Unchecked)

        self.dlg.nextBtn1.clicked.connect(chkSwitch)

    def mainPointLayerComplete(self):
        self.lineFrameObj.readPoint(self.pointFrame)
        self.lineFrameObj.showLayer()

    def mainLineLayerComplete(self):
        self.lineFrameObj = lineFrame.lineCombine(self.lineFrameObj)

    def selectLayerFeature(self):
        c_Feature = self.dlg.tableWidget.selectionModel().selectedIndexes()
        selectedFeatures = list()
        for row in c_Feature:
            selectedFeatures.append(row.row())
        # layer = iface.mapCanvas().currentLayer()
        layer = iface.activeLayer()
        layer.select(selectedFeatures)

    def cancelSelection(self):
        layer = iface.mapCanvas().currentLayer()
        layer.removeSelection()

    def cleanTableSelection(self):
        table = self.dlg.tableWidget
        c_Feature = self.dlg.tableWidget.selectionModel().selectedIndexes()
        columns = table.columnCount()

        for row in c_Feature:
            for j in range(0, columns):
                item = table.item(row.row(), j)
                if item:
                    item.setSelected(False)

    def selectFromQgis(self):
        self.cleanTableSelection()
        layer = iface.activeLayer()
        selectedIds = layer.selectedFeatures()
        columns = self.dlg.tableWidget.columnCount()
        table = self.dlg.tableWidget

        for feature in selectedIds:
            for j in range(0, columns):
                item = table.item(feature.id(), j)
                if item:
                    item.setSelected(True)

    def writeTableToLayer(self):
        layer = iface.activeLayer()

        fieldDict = self.fieldDict
        layerFields = layer.pendingFields()

        Rows = self.dlg.tableWidget.rowCount()
        Columns = self.dlg.tableWidget.columnCount()

        layer.startEditing()

        for i in range(0, Rows):
            for j in range(0, Columns):
                dat = ""
                item = self.dlg.tableWidget.cellWidget(i, j)
                if type(item) == QComboBox:
                    dat = item.currentText()
                elif item is None:
                    if self.dlg.tableWidget.item(i, j) is not None:
                        dat = self.dlg.tableWidget.item(i, j).text()

                fieldName = fieldDict[j]
                idx = layerFields.fieldNameIndex(fieldName)
                #
                # From the data type of layer attribute table, change the
                # text in data table to the same type of attribute field,
                # then fill in the attribute table.
                #
                fieldType = layerFields[idx].typeName()
                if fieldType == 'String':
                    layer.changeAttributeValue(i, idx, dat)

                elif fieldType == 'Integer' and dat:
                    if dat == u'是':
                        dat = 1
                    elif dat == u'否':
                        dat = 0
                    layer.changeAttributeValue(i, idx, int(dat))

                elif fieldType == 'Integer64' and dat:
                    if dat == u'是':
                        dat = long(1)
                    elif dat == u'否':
                        dat = long(0)
                    layer.changeAttributeValue(i, idx, int(dat))

                elif fieldType == 'Real' and dat:
                    layer.changeAttributeValue(i, idx, float(dat))

        layer.commitChanges()

    def setTableToPoly(self, layer):
        def setTableItem(i, j, Object, Type='Object'):
            if type(Object) != QPyNullVariant and Type == 'Object':
                Object = str(Object)
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(Object))
            elif Type == 'ComboBox':
                widget = QComboBox()
                widget.addItem(u'是')
                widget.addItem(u'否')
                if Object == 0:
                    widget.setCurrentIndex(1)
                else:
                    widget.setCurrentIndex(0)
                self.dlg.tableWidget.setCellWidget(i, j, widget)
            else:
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(""))
        registry = QgsMapLayerRegistry.instance()
        vl = registry.mapLayersByName(self.mainLayer.name())
        iface.setActiveLayer(vl[0])

        self.dlg.tableWidget.clear()
        self.dlg.attrSelectBox.clear()

        self.dlg.tableWidget.setRowCount(layer.featureCount())
        self.dlg.tableWidget.setColumnCount(6)
        self.dlg.tableWidget.setHorizontalHeaderLabels([u'網格間距',
                                                        u'符合邊界',
                                                        u'區域分類',
                                                        u'輸出名',
                                                        u'合併網格',
                                                        u'結構化網格'])
        counter = 0
        for feature in layer.getFeatures():
            setTableItem(counter, 0, feature['mesh_size'])
            setTableItem(counter, 1, feature['ForceBound'], Type='ComboBox')
            setTableItem(counter, 2, feature['Physical'])
            setTableItem(counter, 3, feature['geoName'])
            setTableItem(counter, 4, feature['Recombine'], Type='ComboBox')
            setTableItem(counter, 5, feature['Transfinit'], Type='ComboBox')
            counter = counter + 1

        fieldDict = {0: 'mesh_size',
                     1: 'ForceBound',
                     2: 'Physical',
                     3: 'geoName',
                     4: 'Recombine',
                     5: 'Transfinit'}

        self.fieldDict = fieldDict
        self.currentLayer = layer
        self.dlg.attrSelectBox.addItems([u'網格間距',
                                         u'符合邊界',
                                         u'區域分類',
                                         u'輸出名',
                                         u'合併網格',
                                         u'結構化網格'])
        self.tableAttrNameDict = {u'網格間距': 0,
                                  u'符合邊界': 1,
                                  u'區域分類': 2,
                                  u'輸出名': 3,
                                  u'合併網格': 4,
                                  u'結構化網格': 5}

    def setTableToPoint(self, layer):
        def setTableItem(i, j, Object, Type='Object'):
            if type(Object) != QPyNullVariant and Type == 'Object':
                Object = str(Object)
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(Object))
            elif Type == 'ComboBox':
                widget = QComboBox()
                widget.addItem(u'是')
                widget.addItem(u'否')
                if Object == 0:
                    widget.setCurrentIndex(1)
                else:
                    widget.setCurrentIndex(0)
                self.dlg.tableWidget.setCellWidget(i, j, widget)
            elif type(Object) != QPyNullVariant and Type == 'Fixed':
                Object = str(Object)
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(Object))
                item = self.dlg.tableWidget.item(i, j)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            else:
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(""))
        registry = QgsMapLayerRegistry.instance()
        vl = registry.mapLayersByName(self.pointLayer.name())
        iface.setActiveLayer(vl[0])

        self.dlg.tableWidget.clear()
        self.dlg.attrSelectBox.clear()

        self.dlg.tableWidget.setRowCount(layer.featureCount())
        self.dlg.tableWidget.setColumnCount(6)
        self.dlg.tableWidget.setHorizontalHeaderLabels([u'X',
                                                        u'Y',
                                                        u'網格間距',
                                                        u'點分類',
                                                        u'輸出名',
                                                        u'分段點'])
        counter = 0
        for feature in layer.getFeatures():
            setTableItem(counter, 0, feature.geometry().asPoint().x(),
                         Type='Fixed')
            setTableItem(counter, 1, feature.geometry().asPoint().y(),
                         Type='Fixed')
            setTableItem(counter, 2, feature['mesh_size'])
            setTableItem(counter, 3, feature['Physical'])
            setTableItem(counter, 4, feature['geoName'])
            setTableItem(counter, 5, feature['breakPoint'], Type='ComboBox')
            counter = counter + 1

        fieldDict = {0: 'X',
                     1: 'Y',
                     2: 'mesh_size',
                     3: 'Physical',
                     4: 'geoName',
                     5: 'breakPoint'}

        self.fieldDict = fieldDict
        self.currentLayer = layer
        self.dlg.attrSelectBox.addItems([u'網格間距',
                                         u'點分類',
                                         u'輸出名',
                                         u'分段點'])
        self.tableAttrNameDict = {u'X': 0,
                                  u'Y': 1,
                                  u'網格間距': 2,
                                  u'點分類': 3,
                                  u'輸出名': 4,
                                  u'分段點': 5}

    def setTableToLine(self, layer):
        def setTableItem(i, j, Object, Type='Object'):
            if type(Object) != QPyNullVariant and Type == 'Object':
                Object = str(Object)
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(Object))
            elif Type == 'ComboBox':
                widget = QComboBox()
                widget.addItem(u'是')
                widget.addItem(u'否')
                if Object == 0:
                    widget.setCurrentIndex(1)
                else:
                    widget.setCurrentIndex(0)
                self.dlg.tableWidget.setCellWidget(i, j, widget)
            elif type(Object) != QPyNullVariant and Type == 'Fixed':
                Object = str(Object)
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(Object))
                item = self.dlg.tableWidget.item(i, j)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            else:
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(""))
        registry = QgsMapLayerRegistry.instance()
        vl = registry.mapLayersByName(self.lineLayer.name())
        iface.setActiveLayer(vl[0])

        self.dlg.tableWidget.clear()
        self.dlg.attrSelectBox.clear()

        self.dlg.tableWidget.setRowCount(layer.featureCount())
        self.dlg.tableWidget.setColumnCount(5)
        self.dlg.tableWidget.setHorizontalHeaderLabels([u'符合邊界',
                                                        u'邊界性質',
                                                        u'輸出名',
                                                        u'結構化',
                                                        u'切分數量'])
        counter = 0
        for feature in layer.getFeatures():
            setTableItem(counter, 0, feature['ForceBound'], Type='ComboBox')
            setTableItem(counter, 1, feature['Physical'])
            setTableItem(counter, 2, feature['geoName'])
            setTableItem(counter, 3, feature['Transfinit'], Type='ComboBox')
            setTableItem(counter, 4, feature['Cells'])
            counter = counter + 1

        fieldDict = {0: 'ForceBound',
                     1: 'Physical',
                     2: 'geoName',
                     3: 'Transfinit',
                     4: 'Cells'}

        self.fieldDict = fieldDict
        self.currentLayer = layer
        self.dlg.attrSelectBox.addItems([u'符合邊界',
                                         u'邊界性質',
                                         u'輸出名',
                                         u'結構化',
                                         u'切分數量'])
        self.tableAttrNameDict = {u'符合邊界': 0,
                                  u'邊界性質': 1,
                                  u'輸出名': 2,
                                  u'結構化': 3,
                                  u'切分數量': 4}

    def setTableToNodes(self, layer):
        def setTableItem(i, j, Object, Type='Object'):
            if type(Object) != QPyNullVariant and Type == 'Object':
                Object = str(Object)
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(Object))
            elif Type == 'ComboBox':
                widget = QComboBox()
                widget.addItem(u'是')
                widget.addItem(u'否')
                if Object == 0:
                    widget.setCurrentIndex(1)
                else:
                    widget.setCurrentIndex(0)
                self.dlg.tableWidget.setCellWidget(i, j, widget)
            elif type(Object) != QPyNullVariant and Type == 'Fixed':
                Object = str(Object)
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(Object))
                item = self.dlg.tableWidget.item(i, j)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            else:
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(""))
        registry = QgsMapLayerRegistry.instance()
        vl = registry.mapLayersByName("Nodes")
        iface.setActiveLayer(vl[0])

        self.dlg.tableWidget.clear()
        self.dlg.attrSelectBox.clear()

        self.dlg.tableWidget.setRowCount(layer.featureCount())
        self.dlg.tableWidget.setColumnCount(2)
        self.dlg.tableWidget.setHorizontalHeaderLabels([u'高程',
                                                        u'點位性質'])
        counter = 0
        for feature in layer.getFeatures():
            setTableItem(counter, 0, feature['Z'])
            setTableItem(counter, 1, feature['Physical'])
            counter = counter + 1

        fieldDict = {0: 'Z',
                     1: 'Physical'}

        self.fieldDict = fieldDict
        self.currentLayer = layer
        self.dlg.attrSelectBox.addItems([u'高程',
                                         u'點位性質'])
        self.tableAttrNameDict = {u'高程': 0,
                                  u'點位性質': 1}
        layer = iface.activeLayer()
        layer.selectionChanged.connect(self.selectFromQgis)

    def setTableToSegments(self, layer):
        def setTableItem(i, j, Object, Type='Object'):
            if type(Object) != QPyNullVariant and Type == 'Object':
                Object = str(Object)
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(Object))
            elif Type == 'ComboBox':
                widget = QComboBox()
                widget.addItem(u'是')
                widget.addItem(u'否')
                if Object == 0:
                    widget.setCurrentIndex(1)
                else:
                    widget.setCurrentIndex(0)
                self.dlg.tableWidget.setCellWidget(i, j, widget)
            elif type(Object) != QPyNullVariant and Type == 'Fixed':
                Object = str(Object)
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(Object))
                item = self.dlg.tableWidget.item(i, j)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            else:
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(""))
        registry = QgsMapLayerRegistry.instance()
        vl = registry.mapLayersByName("Segments")
        iface.setActiveLayer(vl[0])

        self.dlg.tableWidget.clear()
        self.dlg.attrSelectBox.clear()

        self.dlg.tableWidget.setRowCount(layer.featureCount())
        self.dlg.tableWidget.setColumnCount(1)
        self.dlg.tableWidget.setHorizontalHeaderLabels([u'邊界性質'])
        counter = 0
        for feature in layer.getFeatures():
            setTableItem(counter, 0, feature['Boundary'])
            counter = counter + 1

        fieldDict = {0: 'Boundary'}

        self.fieldDict = fieldDict
        self.currentLayer = layer
        self.dlg.attrSelectBox.addItems([u'邊界性質'])
        self.tableAttrNameDict = {u'邊界性質': 0}

        layer = iface.activeLayer()
        layer.selectionChanged.connect(self.selectFromQgis)

    def attrTable(self, layer, Type='poly'):
        self.dlg.tableWidget.setRowCount(layer.featureCount())

        if Type == 'poly':
            self.setTableToPoly(layer)
        elif Type == 'point':
            self.setTableToPoint(layer)
        elif Type == 'line':
            self.setTableToLine(layer)

    def switchAttr(self, Type):
        if Type == 'poly':
            self.setTableToPoly(self.mainLayer)
        elif Type == 'point':
            self.setTableToPoint(self.pointLayer)
        elif Type == 'line':
            self.setTableToLine(self.lineLayer)
        elif Type == 'Nodes':
            self.setTableToNodes(self.nodeLayer)
        elif Type == 'Segments':
            self.setTableToSegments(self.segLayer)

    def fillBoxFill(self):
        comboxNames = [u'符合邊界',
                       u'合併網格',
                       u'結構化網格',
                       u'分段點',
                       u'結構化']
        currentName = self.dlg.attrSelectBox.currentText()
        self.dlg.fillBox.clear()
        if currentName in comboxNames:
            self.dlg.fillBox.setEditable(False)
            self.dlg.fillBox.addItems([u'是',
                                       u'否'])
        else:
            self.dlg.fillBox.setEditable(True)
            self.dlg.fillBox.clear()

    def readLayerChk(self, lineEdit, switch):
        if not lineEdit.text():
            message = u'請選擇一個圖層檔案'
            detail = u'指指定一個有效的向量圖層檔案'
            self.criticalBox(message, detail)
        else:
            if switch == 1:
                self.readPolyLayer()
            elif switch == 2:
                self.readPointLayer()
            elif switch == 3:
                self.readLineLayer()

    def readPolyLayer(self):
        path = self.dlg.polyIndicator.text()
        layer = iface.addVectorLayer(path, QFileInfo(path).baseName(), 'ogr')
        iface.setActiveLayer(layer)

        self.dlg.polyConfirm.setEnabled(False)
        self.mainLayer = layer
        self.systemCRS = self.mainLayer.dataProvider().crs()
        self.attrTable(layer, Type='poly')
        self.dlg.polyAttrBtn.setEnabled(True)
        self.currentProcess = 1

    def readPointLayer(self):
        path = self.dlg.pointIndicator.text()
        layer = iface.addVectorLayer(path, QFileInfo(path).baseName(), 'ogr')
        iface.setActiveLayer(layer)

        self.dlg.pointConfirm.setEnabled(False)
        self.pointLayer = layer
        self.attrTable(layer, Type='point')
        self.dlg.pointAttrBtn.setEnabled(True)
        self.currentProcess = 2

    def readLineLayer(self):
        path = self.dlg.lineIndicator.text()
        layer = iface.addVectorLayer(path, QFileInfo(path).baseName(), 'ogr')
        iface.setActiveLayer(layer)

        self.dlg.lineConfirm.setEnabled(False)
        self.lineLayer = layer
        self.attrTable(layer, Type='line')
        self.dlg.lineAttrBtn.setEnabled(True)

        lineFrameObj = lineFrame.lineFrame(self.projFolder,
                                           pointLayer=self.pointLayer,
                                           CRS=self.systemCRS)
        self.lineFrameObj = lineFrameObj
        self.currentProcess = 3
        self.dlg.setCompleteBtn.setText(u'合併線段')

    def batchFill(self):
        currentAttrText = self.dlg.attrSelectBox.currentText()
        fillText = self.dlg.fillBox.currentText()
        currentAttrIdx = self.tableAttrNameDict[currentAttrText]

        c_Feature = self.dlg.tableWidget.selectionModel().selectedIndexes()
        selectedFeatures = list()
        for row in c_Feature:
            selectedFeatures.append(row.row())

        for row in selectedFeatures:
            item = self.dlg.tableWidget.cellWidget(row, currentAttrIdx)
            if item:
                if type(item) == QComboBox:
                    if fillText == u'是':
                        item.setCurrentIndex(0)
                    elif fillText == u'否':
                        item.setCurrentIndex(1)
            elif item is None:
                item = self.dlg.tableWidget.item(row, currentAttrIdx)
                if fillText:
                    item.setText(fillText)
                else:
                    item.setText("")

    def processSwitch(self):
        process = self.currentProcess
        if process == 1:
            self.writeTableToLayer()
            self.step2_1()
        elif process == 2:
            self.writeTableToLayer()
            self.step2_2()
        elif process == 3:
            self.writeTableToLayer()
            self.lineFrameObj.frameLayer = self.lineLayer
            self.lineFrameObj.pointFrame = self.pointLayer

            lineFrame.lineCombine(self.lineFrameObj)
            self.setTableToLine(self.lineLayer)
            self.step2_3()
        elif process == 4:
            self.writeTableToLayer()

    def step2(self, source):
        # polygon layer
        try:
            self.attrTable(self.mainLayer, Type='poly')
            self.dlg.polyAttrBtn.setEnabled(True)
        except(AttributeError):
            pass

        self.dlg.resize(self.dlg.maximumSize())
        self.dlg.polyIndicator.setText(source)
        # load polygon layer if button pressed

        try:
            layer = iface.activeLayer()
            layer.selectionChanged.connect(self.selectFromQgis)
        except(AttributeError):
            pass

        self.currentProcess = 1

    def step2_1(self):
        self.orgPoint, self.orgLine = newPointLayer.pointAndLine(self.mainLayer,
                                                                 self.projFolder
                                                                 )
        pointFrameObj = lineFrame.pointFrame(self.projFolder,
                                             orgPointsLayer=self.orgPoint,
                                             CRS=self.systemCRS)
        pointFrameObj.copyPoint()
        pointFrameObj.openLayer()
        pointFrameObj.showLayer()
        self.pointLayer = pointFrameObj.frameLayer

        registry = QgsMapLayerRegistry.instance()
        vl = registry.mapLayersByName(self.pointLayer.name())
        iface.setActiveLayer(vl[0])

        path = self.projFolder + '\\' + 'MainPoint_frame.shp'

        self.attrTable(self.pointLayer, Type='point')
        self.dlg.pointIndicator.setText(path)
        self.dlg.pointAttrBtn.setEnabled(True)
        layer = iface.activeLayer()
        layer.selectionChanged.connect(self.selectFromQgis)
        self.currentProcess = 2

    def step2_2(self):
        lineFrameObj = lineFrame.lineFrame(self.projFolder,
                                           orgLinesLayer=self.orgLine,
                                           pointLayer=self.pointLayer,
                                           CRS=self.systemCRS)
        lineFrameObj.copyLines()
        lineFrameObj.openLayer()
        lineFrameObj.showLayer()

        self.lineLayer = lineFrameObj.frameLayer
        self.lineFrameObj = lineFrameObj

        registry = QgsMapLayerRegistry.instance()
        vl = registry.mapLayersByName(self.lineLayer.name())
        iface.setActiveLayer(vl[0])
        path = self.projFolder + '\\' + 'MainLines_frame.shp'

        self.attrTable(self.lineLayer, Type='line')
        self.dlg.lineIndicator.setText(path)

        self.dlg.lineAttrBtn.setEnabled(True)
        layer = iface.activeLayer()
        layer.selectionChanged.connect(self.selectFromQgis)

        self.currentProcess = 3
        self.dlg.setCompleteBtn.setText(u'合併線段')

    def step2_3(self):
        self.dlg.setCompleteBtn.setText(u'圖層設定完成')
        self.currentProcess = 4
        self.dlg.nextBtn2.clicked.connect(self.step3)

    def step3(self):
        self.dlg.tabWidget.setTabEnabled(2, True)
        self.dlg.tabWidget.setCurrentIndex(2)

    def outputMsh(self):
        OutDir = self.dlg.whereMshLayerEdit.text()
        meshFile = self.dlg.whereMshEdit.text()
        meshOutput(OutDir, meshFile, self.nodeLayer, self.segLayer)

    def resizeDialog(self):
        currentTab = self.dlg.tabWidget.currentIndex()
        if currentTab == 0 or currentTab == 2:
            minSize = self.dlg.minimumSize()
            self.dlg.resize(minSize)
        elif currentTab == 1:
            maxSize = self.dlg.maximumSize()
            self.dlg.resize(maxSize)

    def showMsg(self, P):
        while P.canReadLine():
            line = str(P.readLine())[:-1]
            if "Error" in line:
                self.dlg.textBrowser.setTextColor(QColor(238, 0, 0))
            elif "Warning" in line:
                self.dlg.textBrowser.setTextColor(QColor(0, 139, 69))
            elif "invalid" in line:
                self.dlg.textBrowser.setTextColor(QColor(70, 130, 180))
            else:
                self.dlg.textBrowser.setTextColor(QColor(0, 0, 0))
            self.dlg.textBrowser.append(line)

    def runGMSH(self):
        GMSH = self.dlg.gmshExeEdit.text()
        geoPath = self.dlg.geoEdit.text()
        mshPath = self.dlg.mshEdit.text()

        loopDict = lineFrame.lineToLoop(self.lineFrameObj, self.mainLayer)
        genGeo(self.projFolder, self.mainLayer, self.pointLayer,
               self.lineFrameObj, loopDict, geoPath)

        P = QProcess()
        P.setProcessChannelMode(QProcess.MergedChannels)
        P.readyReadStandardOutput.connect(lambda: self.showMsg(P))

        env = QProcessEnvironment.systemEnvironment()
        env.remove("TERM")
        P.setProcessEnvironment(env)
        command = GMSH + " " + geoPath + " -2 -o " + mshPath
        command = command.replace('/', '\\')
        P.start(command)

        self.dlg.textBrowser.setText(command)

    def loadGeneratedMesh(self):
        refId = QgsCoordinateReferenceSystem.PostgisCrsId
        if not self.systemCRS:
            systemCRS = QgsCoordinateReferenceSystem(3826, refId)
        else:
            systemCRS = self.systemCRS
        meshFile = self.dlg.whereMshEdit.text()
        outDir = self.dlg.whereMshLayerEdit.text()
        loadMesh(meshFile, systemCRS, outDir, self.dlg)

        Instance = QgsMapLayerRegistry.instance()
        NodeLayer = Instance.mapLayersByName("Nodes")[0]
        iface.setActiveLayer(NodeLayer)
        self.setTableToNodes(NodeLayer)
        self.nodeLayer = NodeLayer

        SegmentLayer = Instance.mapLayersByName("Segments")[0]
        self.segLayer = SegmentLayer
        self.dlg.meshOutputBtn.setEnabled(True)

    def changeTo2dm(self):

        userFolder = os.path.expanduser("~")
        appFolder = userFolder + "\\.qgis2\\python\\plugins\\meshBuilder"
        os.chdir(appFolder)

        path2dm = self.dlg.where2dmEdit.text()
        mshPath = self.dlg.whereMshEdit.text()

        ibcName = os.path.basename(path2dm).replace('.2dm', '.ibc')
        dirname = os.path.dirname(path2dm)
        ibcPath = dirname + "\\" + ibcName
        if os.path.isfile(ibcPath):
            command = "GMSH2SRH.exe" + " " + mshPath + " " + path2dm + " " + ibcPath
        else:
            command = "GMSH2SRH.exe" + " " + mshPath + " " + path2dm

        os.system(command)

    def mshInterp(self):
        def writeMsgToLabel(P):
            while P.canReadLine():
                line = u'執行中...' + str(P.readLine())[:-1]
                self.dlg.label_19.setText(line)

        def onFinished():
            self.dlg.label_19.setText(u'完成')
            self.dlg.whereMshEdit.setText(Path)

        Path = self.dlg.whereInterpEdit.text()
        mshPath = self.dlg.whereMshEdit.text()

        os.chdir(os.path.expanduser('~') + "\\.qgis2\\python\\plugins\\" +
                 "meshBuilder")

        P = QProcess()
        P.setProcessChannelMode(QProcess.MergedChannels)
        P.readyReadStandardOutput.connect(lambda: writeMsgToLabel(P))

        env = QProcessEnvironment.systemEnvironment()
        env.remove("TERM")
        P.setProcessEnvironment(env)
        command = "ZInterporate.exe" + " " + mshPath + " TW40M.xyz " + Path
        command = command.replace('/', '\\')
        P.start(command)
        P.finished.connect(onFinished)

    def warningBox(self, title, message, lineEdit, lineEditText):

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle(title)
        msg.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        val = msg.exec_()
        if val == QMessageBox.Yes:
            lineEdit.setText(lineEditText)
        elif val == QMessageBox.No:
            lineEdit.clear()

    def criticalBox(self, title, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(message)
        msg.setWindowTitle(title)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def dirEmpty(self, directory, message, detail, lineEdit, lineEditText):
        try:
            files = os.listdir(directory)
            files.remove("MainLayers")
            files.remove("InnerLayers")
            if files:
                self.warningBox(message, detail, lineEdit, lineEditText)
        except(WindowsError, ValueError):
            pass

    def run(self):
        refId = QgsCoordinateReferenceSystem.PostgisCrsId
        self.systemCRS = QgsCoordinateReferenceSystem(3826, refId)
        self.dlg.lineEdit.clear()
        caption = u'請選擇一個專案資料夾'
        self.dlg.FileBrowseBtn.clicked.connect(lambda: self.folderBrowser(caption,
                                                                          lineEdit=self.dlg.lineEdit))
        projFoldMsg = u'指定的專案資料夾不是空的'
        projFoldDetail = u'指定的專案資料夾不是空的!\n若設定此資料夾為專案資料\
夾，則資料夾內的資料將被清除。\n請問是否繼續？'
        self.dlg.lineEdit.textChanged.connect(lambda: self.dirEmpty(self.dlg.lineEdit.text(),
                                                                    projFoldMsg,
                                                                    projFoldDetail,
                                                                    self.dlg.lineEdit,
                                                                    self.dlg.lineEdit.text()))

        self.dlg.polyIndicator.clear()
        self.dlg.pointIndicator.clear()
        self.dlg.lineIndicator.clear()

        """Run method that performs all the real work"""
        self.dlg.tabWidget.setCurrentIndex(0)
        # Set step2, step3 tab temporary unaccessible
        self.dlg.tabWidget.setTabEnabled(1, False)
        self.dlg.tabWidget.setTabEnabled(2, False)
        self.dlg.outputMeshPointsBtn.setEnabled(False)
        self.dlg.outputSegmentsBtn.setEnabled(False)
        self.dlg.meshOutputBtn.setEnabled(False)

        self.dlg.tabWidget.currentChanged.connect(self.resizeDialog)

        # show the dialog
        self.dlg.show()
        self.dlg.resize(self.dlg.minimumSize())
        self.step1()

        self.dlg.tableWidget.cellClicked.connect(self.selectLayerFeature)
        self.dlg.tableWidget.currentCellChanged.connect(self.cancelSelection)
        self.dlg.attrSelectBox.currentIndexChanged.connect(self.fillBoxFill)
        self.dlg.batchFillBtn.clicked.connect(self.batchFill)
        self.dlg.writeLayerBtn.clicked.connect(self.writeTableToLayer)
        self.dlg.setCompleteBtn.clicked.connect(self.processSwitch)

        self.dlg.polyAttrBtn.clicked.connect(lambda: self.switchAttr('poly'))
        self.dlg.pointAttrBtn.clicked.connect(lambda: self.switchAttr('point'))
        self.dlg.lineAttrBtn.clicked.connect(lambda: self.switchAttr('line'))
        self.dlg.polyAttrBtn.setEnabled(False)
        self.dlg.pointAttrBtn.setEnabled(False)
        self.dlg.lineAttrBtn.setEnabled(False)
        self.dlg.gmshExeBtn.clicked.connect(self.runGMSH)

        Caption = u"請選擇一個多邊形圖層"
        lineEdit = self.dlg.polyIndicator
        wherePolyBtn = self.dlg.wherePolyBtn
        wherePolyBtn.clicked.connect(lambda: self.fileBrowser(Caption,
                                                              self.projFolder,
                                                              lineEdit=lineEdit))
        p_Caption = u"請選擇一個點圖層"
        wherePointBtn = self.dlg.wherePointBtn
        p_lineEdit = self.dlg.pointIndicator
        wherePointBtn.clicked.connect(lambda: self.fileBrowser(p_Caption,
                                                               self.projFolder,
                                                               lineEdit=p_lineEdit))
        l_Caption = u"請選擇一個線圖層"
        whereLineBtn = self.dlg.whereLineBtn
        l_lineEdit = self.dlg.lineIndicator
        whereLineBtn.clicked.connect(lambda: self.fileBrowser(l_Caption,
                                                              self.projFolder,
                                                              lineEdit=l_lineEdit))
        g_Caption = u'請選擇GMSH.exe的檔案位置'
        whereGMSH = self.dlg.whereGMSH
        gmshExeEdit = self.dlg.gmshExeEdit
        whereGMSH.clicked.connect(lambda: self.fileBrowser(g_Caption, os.getcwd(),
                                                           lineEdit=gmshExeEdit,
                                                           presetType='.exe'))
        geoCaption = u'請選擇產生.geo檔案的檔名及資料夾'
        whereGeo = self.dlg.whereGeo
        geoEdit = self.dlg.geoEdit
        try:
            destFolder = self.projFolder
        except(AttributeError):
            destFolder = os.path.expanduser("~")
        whereGeo.clicked.connect(lambda: self.saveFileBrowser(geoCaption,
                                                              destFolder,
                                                              lineEdit=geoEdit,
                                                              presetType='.geo'))

        mshCaption = u'請選擇輸出網格檔案的資料夾及檔案路徑'
        mshEdit = self.dlg.mshEdit
        whereMsh = self.dlg.whereMsh
        whereMsh.clicked.connect(lambda: self.saveFileBrowser(mshCaption,
                                                              destFolder,
                                                              lineEdit=mshEdit,
                                                              presetType='.msh'))

        loadMshCaption = u'請選擇一個.msh檔案'
        whereMshEdit = self.dlg.whereMshEdit
        whereMshBtn = self.dlg.whereMshBtn
        whereMshBtn.clicked.connect(lambda: self.fileBrowser(loadMshCaption,
                                                             os.path.expanduser("~"),
                                                             lineEdit=whereMshEdit,
                                                             presetType='.msh'))
        MshLayerCaption = u'請選擇建立讀入網格圖層的資料夾'
        whereMshLayerEdit = self.dlg.whereMshLayerEdit
        whereMshLayerBtn = self.dlg.whereMshLayerBtn
        whereMshLayerBtn.clicked.connect(lambda: self.folderBrowser(MshLayerCaption,
                                                                    os.path.expanduser("~"),
                                                                    whereMshLayerEdit))

        interpMshCaption = u'請選擇要內插高程的網格檔案'
        whereInterpEdit = self.dlg.whereInterpEdit
        whereInterpBtn = self.dlg.whereInterpBtn
        whereInterpBtn.clicked.connect(lambda: self.saveFileBrowser(interpMshCaption,
                                                                    os.path.expanduser("~"),
                                                                    lineEdit=whereInterpEdit,
                                                                    presetType='.msh'))

        where2dmCaption = u'請選擇 .msh 檔案轉 .2dm 檔案的輸出位置'
        where2dmEdit = self.dlg.where2dmEdit
        where2dmBtn = self.dlg.where2dmBtn
        where2dmBtn.clicked.connect(lambda: self.saveFileBrowser(where2dmCaption,
                                                                 os.path.expanduser("~"),
                                                                 lineEdit=where2dmEdit,
                                                                 presetType='.2dm'))

        self.dlg.polyConfirm.clicked.connect(lambda: self.readLayerChk(self.dlg.polyIndicator, 1))
        self.dlg.pointConfirm.clicked.connect(lambda: self.readLayerChk(self.dlg.pointIndicator, 2))
        self.dlg.lineConfirm.clicked.connect(lambda: self.readLayerChk(self.dlg.lineIndicator, 3))
        self.dlg.loadMshBtn.clicked.connect(self.loadGeneratedMesh)
        self.dlg.outputMeshPointsBtn.clicked.connect(lambda: self.switchAttr('Nodes'))
        self.dlg.outputSegmentsBtn.clicked.connect(lambda: self.switchAttr('Segments'))
        self.dlg.meshOutputBtn.clicked.connect(self.outputMsh)
        self.dlg.interpExecBtn.clicked.connect(self.mshInterp)
        self.dlg.to2dmExecBtn.clicked.connect(self.changeTo2dm)
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass


mshTypeRef = {15: 1, 1: 2, 2: 3, 3: 4, 4: 5}


def loadMesh(filename, crs, outDir, dlg):
    meshfile = open(filename, 'r')
    meshName = filename.split('/')[-1]
    mesh = meshfile.readlines()
    SegList = lineFrame.lineRefDict()

    vertices = dict()
    physicalNames = dict()
    layerPath = dict()
    physicalWriter = dict()
    NodeFeature = dict()
    mode = 0
    endStatements = ["$EndPhysicalNames", "$EndNodes", "$EndElements"]

    fields = QgsFields()
    fields.append(QgsField("id", QVariant.Int))
    nodePath = outDir + "\\" + "Nodes.shp"
    NodeFields = QgsFields()
    NodeFields.append(QgsField("id", QVariant.Int))
    NodeFields.append(QgsField("Z", QVariant.Double))
    NodeFields.append(QgsField("Physical", QVariant.String))
    NodeWriter = QgsVectorFileWriter(nodePath, "UTF-8", NodeFields,
                                     QGis.WKBPoint, crs, "ESRI Shapefile")
    SegFields = QgsFields()
    SegFields.append(QgsField("id", QVariant.Int))
    SegFields.append(QgsField("Boundary", QVariant.String))
    SegPath = outDir + "\\" + "Segments.shp"
    SegWriter = QgsVectorFileWriter(SegPath, "UTF-8", SegFields,
                                    QGis.WKBLineString, crs, "ESRI Shapefile")
    counter = 0
    for l in mesh:
        w = l.split()

        if w[0] == "$PhysicalNames":
            mode = 1
        elif w[0] == "$Nodes":
            mode = 2
        elif w[0] == "$Elements":
            mode = 3
        elif w[0] in endStatements:
            continue

        if mode == 1 and len(w) > 1:
            dim, tag, name = int(w[0]), int(w[1]), w[2]
            name = name[1:-1]
            physicalNames.update({tag: [int(dim), name]})
            path = outDir + "\\" + name + ".shp"

            # Create QGIS layers
            if dim == 0:
                layerType = QGis.WKBPoint
            elif dim == 1:
                layerType = QGis.WKBLineString
            elif dim >= 2:
                layerType = QGis.WKBPolygon
            writer = QgsVectorFileWriter(path, "UTF-8", fields, layerType,
                                         crs, "ESRI Shapefile")
            writer.path = path
            physicalWriter.update({tag: writer})
            layerPath.update({tag: path})

        elif mode == 2 and len(w) > 1:
            nid, x, y, z = w[0], w[1], w[2], w[3]
            vertices.update({int(nid): (float(x), float(y), float(z))})
            feature = QgsFeature()
            WktString = "POINT (" + x + " " + y + ")"
            NodeFeature.update({int(nid): [WktString, float(z), None]})
        elif mode == 3 and len(w) > 1:
            fid = int(w[0])
            geoType = int(w[1])
            tagsNum = int(w[2])
            tagArgs = w[3:3+tagsNum]
            NodesNum = mshTypeRef[geoType]
            ElementNodes = w[3+tagsNum:3+tagsNum+NodesNum]

            writer = physicalWriter[int(tagArgs[0])]
            feature = QgsFeature()
            if NodesNum == 1:
                point = NodeFeature[int(ElementNodes[0])][0]
                feature.setGeometry(QgsGeometry().fromWkt(point))
                nodeName = physicalNames[int(tagArgs[0])][1]
                NodeFeature[int(ElementNodes[0])][2] = nodeName
            elif NodesNum == 2:
                x1, y1, z1 = vertices[int(ElementNodes[0])]
                x2, y2, z2 = vertices[int(ElementNodes[1])]
                geoString = "LINESTRING ("
                geoString = geoString + str(x1) + " " + str(y1) + ","
                geoString = geoString + str(x2) + " " + str(y2)
                geoString = geoString + ")"
                feature.setGeometry(QgsGeometry().fromWkt(geoString))
                try:
                    SegList[int(ElementNodes[0]), int(ElementNodes[1])]
                except(KeyError):
                    x1, y1, z1 = vertices[int(ElementNodes[0])]
                    x2, y2, z2 = vertices[int(ElementNodes[1])]
                    WktString = ("LINESTRING (" + str(x1) + " " + str(y1) + ",")
                    WktString = WktString + str(x2) + " " + str(y2) + ")"
                    boundName = physicalNames[int(tagArgs[0])][1]
                    SegList.update({(int(ElementNodes[0]),
                                     int(ElementNodes[1])):
                                    [WktString, boundName]})
            elif NodesNum > 2:
                geoString = "POLYGON (("
                ElementNodes.append(ElementNodes[0])
                for pid in ElementNodes:
                    x, y, z = vertices[int(pid)]
                    geoString = geoString + str(x) + " " + str(y) + ","
                geoString = geoString[:-1] + "))"
                feature.setGeometry(QgsGeometry().fromWkt(geoString))

                for i in range(1, len(ElementNodes)):
                    try:
                        SegList[(int(ElementNodes[i-1]), int(ElementNodes[i]))]
                    except(KeyError):
                        x1, y1, z1 = vertices[int(ElementNodes[i-1])]
                        x2, y2, z2 = vertices[int(ElementNodes[i])]
                        WktString = ("LINESTRING (" + str(x1) + " " + str(y1) +
                                     ",")
                        WktString = WktString + str(x2) + " " + str(y2) + ")"
                        SegList.update({(int(ElementNodes[i-1]),
                                         int(ElementNodes[i])):
                                        [WktString, None]})

            feature.setAttributes([int(fid)])
            writer.addFeature(feature)
        elif mode == 0:
            continue
        elif len(w) == 1:
            continue
        counter = counter + 1
        dlg.meshLoadProgress.setValue(int(float(counter)/len(mesh)*100))

    maxTag = max(layerPath.keys())
    for writer in physicalWriter.values():
        del writer

    for key in NodeFeature.keys():
        feature = QgsFeature()
        geoString = NodeFeature[key][0]
        Z = NodeFeature[key][1]
        phys = NodeFeature[key][2]
        feature.setGeometry(QgsGeometry().fromWkt(geoString))
        feature.setAttributes([key, Z, phys])
        NodeWriter.addFeature(feature)

    del NodeWriter

    layerPath.update({maxTag+1: nodePath})
    NodeLayer = QgsVectorLayer(nodePath, QFileInfo(nodePath).baseName(), 'ogr')

    id_tag = 0
    for key in SegList.keys():
        lineString = SegList[key][0]
        boundName = SegList[key][1]
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry().fromWkt(lineString))
        feature.setAttributes([id_tag, boundName])
        SegWriter.addFeature(feature)
    del SegWriter

    SegLayer = QgsVectorLayer(SegPath, QFileInfo(SegPath).baseName(), 'ogr')

    layerPath.update({maxTag+2: SegPath})
    dlg.meshLoadProgress.setValue(100)
    loadMeshLayers(layerPath, meshName, NodeLayer, SegLayer)

    size = dlg.maximumSize()
    dlg.resize(size)
    dlg.pointAttrBtn.setDisabled(True)
    dlg.lineAttrBtn.setDisabled(True)
    dlg.polyAttrBtn.setDisabled(True)
    dlg.setCompleteBtn.setDisabled(True)
    dlg.outputMeshPointsBtn.setEnabled(True)
    dlg.outputSegmentsBtn.setEnabled(True)


def loadMeshLayers(layerPath, meshName, NodeLayer, SegLayer):
    meshName.replace('.msh', '')
    group = QgsProject.instance().layerTreeRoot().addGroup(meshName)

    layers = list()
    for path in layerPath.values():
        layer = QgsVectorLayer(path, QFileInfo(path).baseName(), 'ogr')
        layers.append(layer)
        QgsMapLayerRegistry.instance().addMapLayer(layer, False)
        group.addLayer(layer)


def physicCode(physName, physicsRef):
    for key in physicsRef.keys():
        if physicsRef[key][0] == physName:
            return key


def arangeNodeLines(NodeLayer, physicsRef):
    physicalNodes = list()
    for feature in NodeLayer.getFeatures():
        if feature['Physical'] != None:
            physName = feature['Physical']
            ref = physicCode(physName, physicsRef)
            line = "15 2 " + str(ref) + " 0 " + str(feature.id() + 1) + "\n"
            physicalNodes.append(line)
    return physicalNodes


def arangeSegLines(SegLayer, physicsRef, nodeRef):
    physicalSegs = list()
    for feature in SegLayer.getFeatures():
        if feature['Boundary'] != None:
            lineGeo = feature.geometry().asPolyline()
            id1 = nodeRef[lineGeo[0]]
            id2 = nodeRef[lineGeo[-1]]
            physName = feature['Boundary']
            ref = physicCode(physName, physicsRef)
            line = "1 2 " + str(ref) + " 0 " + str(id1) + " " + str(id2) + "\n"
            physicalSegs.append(line)
    return physicalSegs


def arangeMesh(OutDir, gridNames, physicsRef, nodeRef):
    meshLines = list()
    for name in gridNames:
        ref = physicCode(name, physicsRef)
        layername = OutDir + "\\" + name + ".shp"
        layer = QgsVectorLayer(layername, QFileInfo(layername).baseName(),
                               'ogr')
        for feature in layer.getFeatures():
            geo = feature.geometry().asPolygon()
            geo[0].pop(-1)
            line = str(len(geo[0])-1) + " 2 " + str(ref) + " 0 "

            for point in geo[0]:
                fid = nodeRef[point]
                line = line + str(fid) + " "
            line = line[:-1] + "\n"
            meshLines.append(line)

    return meshLines


def getGridNames(OutDir, NodeLayer, SegLayer):
    gridNames = list()
    fileNames = os.listdir(OutDir)
    for name in fileNames:
        if ".shp" in name:
            name = OutDir + "\\" + name
            layer = QgsVectorLayer(name, QFileInfo(name).baseName(), 'ogr')
            if layer.geometryType() == QGis.Polygon:
                gridNames.append(QFileInfo(name).baseName())
            del layer

    pointPhysics = list()
    for feature in NodeLayer.getFeatures():
        if feature['Physical'] != None:
            pointPhysics.append(feature['Physical'])
    pointPhysics = set(pointPhysics)

    linePhysics = list()
    for feature in SegLayer.getFeatures():
        if feature['Boundary'] != None:
            linePhysics.append(feature['Boundary'])
    linePhysics = set(linePhysics)

    return pointPhysics, linePhysics, gridNames


def meshOutput(OutDir, meshFile, NodeLayer, SegLayer):
    physicsRef = dict()
    nodeRef = lineFrame.pointRefDict()
    pointPhysics, linePhysics, gridNames = getGridNames(OutDir, NodeLayer,
                                                        SegLayer)
    counter = 1
    if pointPhysics:
        for physic in pointPhysics:
            physicsRef.update({counter: [physic, 0]})
            counter = counter + 1
    if linePhysics:
        for physic in linePhysics:
            physicsRef.update({counter: [physic, 1]})
            counter = counter + 1
    if gridNames:
        for physic in gridNames:
            physicsRef.update({counter: [physic, 2]})
            counter = counter + 1

    f = open(meshFile, 'w')
    f.write("$MeshFormat\n")
    f.write("2.2 0 8\n")
    f.write("$EndMeshFormat\n")
    f.write("$PhysicalNames\n")
    f.write(str(len(physicsRef.values())) + "\n")
    for i in range(1, counter):
        PhysName = physicsRef[i][0]  # Name of physics
        Dim = physicsRef[i][1]  # Dimension of physics
        f.write(str(Dim) + " " + str(i) + " " + '"' + PhysName + '"\n')
    f.write("$EndPhysicalNames\n")
    f.write("$Nodes\n")
    f.write(str(NodeLayer.featureCount()) + "\n")
    for feature in NodeLayer.getFeatures():
        fid = feature.id() + 1
        x = feature.geometry().asPoint().x()
        y = feature.geometry().asPoint().y()
        nodeRef.update({QgsPoint(x, y): fid})
        z = feature["Z"]
        f.write(str(fid) + " " + str(x) + " " + str(y) + " " + str(z) + '\n')
    f.write("$EndNodes\n")

    physicalNodes = arangeNodeLines(NodeLayer, physicsRef)
    physicalNodes.sort()
    physicalSegs = arangeSegLines(SegLayer, physicsRef, nodeRef)
    physicalSegs.sort()
    meshes = arangeMesh(OutDir, gridNames, physicsRef, nodeRef)
    meshes.sort()
    meshes.sort(key=len)

    f.write("$Elements\n")
    f.write(str(len(physicalNodes)+len(physicalSegs)+len(meshes)) + "\n")
    elementCount = 1
    for line in physicalNodes:
        f.write(str(elementCount) + " " + line)
        elementCount = elementCount + 1
    for line in physicalSegs:
        f.write(str(elementCount) + " " + line)
        elementCount = elementCount + 1
    for line in meshes:
        f.write(str(elementCount) + " " + line)
        elementCount = elementCount + 1

    f.write("$EndElements")
    f.close()
