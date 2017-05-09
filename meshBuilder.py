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
from PyQt4.QtCore import QFileInfo, QPyNullVariant, QVariant
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QListWidgetItem
from qgis.core import QgsVectorLayer
from PyQt4.QtGui import QTableWidgetItem, QComboBox
from qgis.utils import iface
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from meshBuilder_dialog import meshBuilderDialog
import os.path
import newPointLayer
import lineFrame
from innerLayers import innerLayersExport
import shutil
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

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Mesh Builder')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'meshBuilder')
        self.toolbar.setObjectName(u'meshBuilder')

        self.dlg.lineEdit.clear()
        self.dlg.FileBrowseBtn.clicked.connect(self.folderBrowser)

        self.dlg.polyIndicator.clear()
        self.dlg.pointIndicator.clear()
        self.dlg.lineIndicator.clear()

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


    def add_action(
        self,
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
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/meshBuilder/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u''),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Mesh Builder'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def folderBrowser(self):
        folderName = QFileDialog.getExistingDirectory(self.dlg,
                                                      "Select Project Folder")
        if folderName:
            self.dlg.lineEdit.setText(folderName)

    def fileBrowser(self):
        Caption = self.c_Caption
        lineEdit = self.c_lineEdit
        fileName = QFileDialog.getOpenFileName(self.dlg, Caption,
                                               self.projFolder, "*.shp")
        if fileName:
            lineEdit.setText(fileName)

    def cleanProjFolder(self, projFolder):
        files = os.listdir(projFolder)
        for name in files:
            if os.path.isfile(projFolder + "\\" + name):
                os.remove(projFolder + "\\" + name)

        if os.path.isdir(projFolder + '\\MainLayers'):
            files = os.listdir(projFolder + '\\MainLayers')
            for name in files:
                os.remove(projFolder + '\\MainLayers' + "\\" + name)
        else:
            os.mkdir(projFolder + '\\MainLayers')

        if os.path.isdir(projFolder + '\\InnerLayers'):
            files = os.listdir(projFolder + '\\InnerLayers')
            for name in files:
                os.remove(projFolder + '\\InnerLayers' + "\\" + name)
        else:
            os.mkdir(projFolder + '\\InnerLayers')

    def step1_1(self):

        projFolder = str(self.dlg.lineEdit.text())
        self.projFolder = projFolder
        self.cleanProjFolder(projFolder)

        layers = self.iface.legendInterface().layers()

        MainName = self.dlg.comboBox.currentText()
        for layer in layers:
            if layer.name() == MainName:
                mainLayerSelected = layer
        self.systemCRS = mainLayerSelected.dataProvider().crs()

        newMainLayer = newPointLayer.copyMainLayer(mainLayerSelected,
                                                   projFolder)
        self.mainLayer = newMainLayer
        newMainLayer.setCrs(self.systemCRS)
        source = newMainLayer.dataProvider().dataSourceUri().split('|')[0]
        #  Load the assinged shape file layer into qgis, and show on the canvas.
        iface.addVectorLayer(source, QFileInfo(source).baseName(), 'ogr')

        innerLayersChecked = list()
        for i in range(0, self.dlg.listWidget.count()):
            item = self.dlg.listWidget.item(i)
            if item.checkState() == Qt.Checked:
                innerLayersChecked.append(item.text())
        innerLayersList = list()
        for layer in layers:
            if layer.name() in innerLayersChecked:
                innerLayersList.append(layer)

        innerLayers = innerLayersExport(projFolder, newMainLayer)
        innerLayers.innerLayers = innerLayersList
        innerLayers.copyLayers()

        """
        pointFrame = lineFrame.pointFrame(projFolder, orgPointsLayer=pointLayer)
        pointFrame.copyPoint()
        pointFrame.openLayer()
        self.pointFrame = pointFrame

        lineFrameObj = lineFrame.lineFrame(projFolder, orgLinesLayer=lineLayer)
        lineFrameObj.copyLines()
        lineFrameObj.openLayer()
        self.lineFrameObj = lineFrameObj"""

        self.dlg.tabWidget.setTabEnabled(1, True)
        self.dlg.tabWidget.setCurrentIndex(1)
        self.step2(source)

    def step1(self):
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

        self.dlg.NextBtn1.clicked.connect(self.step1_1)

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
        layer = iface.mapCanvas().currentLayer()
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
        fieldDict = self.fieldDict
        layer = self.currentLayer
        layerFields = layer.pendingFields()

        Rows = self.dlg.tableWidget.rowCount()
        Columns = self.dlg.tableWidget.columnCount()

        layer.startEditing()

        item = self.dlg.tableWidget.cellWidget(0, 2)
        for i in range(0, Rows):
            for j in range(0, Columns):
                item = self.dlg.tableWidget.cellWidget(i, j)
                if type(item) == QComboBox:
                    dat = item.currentText()
                elif item is None:
                    dat = self.dlg.tableWidget.item(i, j).text()

                fieldName = fieldDict[j]
                idx = layerFields.fieldNameIndex(fieldName)

                fieldType = layerFields[idx].typeName()
                if fieldType == 'String':
                    layer.changeAttributeValue(i, idx, dat)
                elif fieldType == 'Integer' and dat:
                    if dat == u'是':
                        dat = 1
                    elif dat == u'否':
                        dat = 0
                    layer.changeAttributeValue(i, idx, int(dat))
                elif fieldType == 'Real' and dat:
                    layer.changeAttributeValue(i, idx, float(dat))

        layer.commitChanges()

    def setTableToPoly(self, layer):
        def setTableItem(i, j, Object, Type='Object'):
            if type(Object) != QPyNullVariant and Type == 'Object':
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

        fieldDict = {0:'mesh_size',
                        1:'ForceBound',
                        2:'Physical',
                        3:'geoName',
                        4:'Recombine',
                        5:'Transfinit'}

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

    def attrTable(self, layer, Type='poly'):
        self.dlg.tableWidget.setRowCount(layer.featureCount())

        if Type == 'poly':
            self.setTableToPoly(layer)

    def fillBoxFill(self):
        comboxNames = [u'符合邊界', u'合併網格', u'結構化網格']
        currentName = self.dlg.attrSelectBox.currentText()
        self.dlg.fillBox.clear()
        if currentName in comboxNames:
            self.dlg.fillBox.setEditable(False)
            self.dlg.fillBox.addItems([u'是', u'否'])
        else:
            self.dlg.fillBox.setEditable(True)
            self.dlg.fillBox.clear()

    def readPolyLayer(self):
        path = self.dlg.polyIndicator.text()
        layer = iface.addVectorLayer(path, QFileInfo(path).baseName(), 'ogr')

        self.dlg.polyConfirm.setEnabled(False)
        self.mainLayer = layer
        self.attrTable(layer, Type='poly')

    def batchFill(self):
        tableAttrNameDict = self.tableAttrNameDict
        currentAttrIdx = self.dlg.attrSelectBox.currentIndex()
        fillText = self.dlg.fillBox.currentText()

        c_Feature = self.dlg.tableWidget.selectionModel().selectedIndexes()
        selectedFeatures = list()
        for row in c_Feature:
            selectedFeatures.append(row.row())

        for row in selectedFeatures:
            item = self.dlg.tableWidget.cellWidget(row, currentAttrIdx)
            if item:
                self.dlg.label_3.setText(str(type(item)))
                if type(item) == QComboBox:
                    if fillText == u'是':
                        item.setCurrentIndex(0)
                    elif fillText == u'否':
                        item.setCurrentIndex(1)
            elif item is None:
                item = self.dlg.tableWidget.item(row, currentAttrIdx)
                item.setText(fillText)

    def step2(self, source):
        # polygon layer
        self.attrTable(self.mainLayer, Type='poly')

        self.dlg.resize(self.dlg.maximumSize())
        self.dlg.polyIndicator.setText(source)
        self.c_Caption = "Select a polygon shapefile"
        self.c_lineEdit = self.dlg.polyIndicator
        self.dlg.wherePolyBtn.clicked.connect(self.fileBrowser)
        # load polygon layer if button pressed
        self.dlg.polyConfirm.clicked.connect(self.readPolyLayer)
        self.dlg.polyAttrBtn.setEnabled(False)
        self.dlg.writeLayerBtn.clicked.connect(self.writeTableToLayer)
        layer = iface.activeLayer()
        layer.selectionChanged.connect(self.selectFromQgis)
        self.dlg.tableWidget.cellClicked.connect(self.selectLayerFeature)
        self.dlg.tableWidget.currentCellChanged.connect(self.cancelSelection)
        self.dlg.attrSelectBox.currentIndexChanged.connect(self.fillBoxFill)
        self.dlg.batchFillBtn.clicked.connect(self.batchFill)

    def run(self):
        """Run method that performs all the real work"""
        # Set step2, step3 tab temporary unaccessible
        self.dlg.tabWidget.setTabEnabled(1, False)
        self.dlg.tabWidget.setTabEnabled(2, False)

        # show the dialog
        self.dlg.show()
        self.dlg.resize(self.dlg.minimumSize())
        self.step1()

        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
