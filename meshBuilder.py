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
from PyQt4.QtGui import QAction, QIcon, QListWidgetItem, QColor
from PyQt4.QtGui import QTableWidgetItem, QComboBox, QLineEdit, QPixmap
from qgis.core import QgsVectorLayer, QgsMapLayerRegistry, QgsVectorFileWriter
from qgis.core import QgsGeometry, QgsFeature, QGis, QgsFields, QgsField
from qgis.core import QgsCoordinateReferenceSystem, QgsProject, QgsPoint
from qgis.core import QgsMessageLog, QgsSymbolV2, QgsRuleBasedRendererV2
from qgis.gui import QgsMessageBar, QgsGenericProjectionSelector
from qgis.utils import iface
from lineFlip import flip
from commonDialog import fileBrowser, folderBrowser, saveFileBrowser
from commonDialog import onCritical, onWarning
from random import randint
# Import the code for the dialog
from meshBuilder_dialog import meshBuilderDialog
from .srhpre import shepred
import os.path
import newPointLayer
import lineFrame
import subprocess
import re
from innerLayers import innerLayersExport
from exportToGeo import genGeo
from shutil import rmtree
from collections import Counter
from copy import copy
from operator import itemgetter
from loadPara import loadParaView
from mesh2DViewer import mesh2DView
from zoneOrdDiag import zoneSeqIterator
from selectorDiag import loadSelector
from itertools import izip as zip, count
from toUnicode import toUnicode
import os
import pickle
# Initialize Qt resources from file resources.py
import resources
import plus_rc


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
        self.srhpre = shepred.shepred(self.iface)
        self.mesh2D = mesh2DView(self.iface)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Mesh Builder')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'meshBuilder')
        self.toolbar.setObjectName(u'meshBuilder')

        try:
            parameterPath = os.path.join(os.path.dirname(__file__),
                                         '__parameter__')
            f = open(parameterPath, 'rb')
            param = pickle.load(f)
            f.close()
        except:
            param = dict()
            param.update({'GMSH': ''})
            param.update({'projFolder': ''})
        self.__parameter__ = param

		# WRA 修改預設資料夾： 改變 120 行的 Dir='目標資料夾'
        caption = u'請選擇一個專案資料夾'
        self.dlg.FileBrowseBtn.pressed.connect(
            lambda: folderBrowser(self.dlg,
                                  caption, Dir=self.dlg.lineEdit.text(),
                                  lineEdit=self.dlg.lineEdit))
        self.dlg.FileBrowseBtn.setToolTip(caption)

        self.dlg.lineEdit.textChanged.connect(
            lambda: self.dirEmpty(self.dlg.lineEdit.text(),
                                  self.dlg.lineEdit, self.dlg.lineEdit.text()))

        QgsMapLayerRegistry.instance().legendLayersAdded.connect(self.step1)

        self.dlg.tabWidget.currentChanged.connect(self.resizeDialog)
        self.dlg.tableWidget.cellClicked.connect(self.selectLayerFeature)
        self.dlg.tableWidget.currentCellChanged.connect(self.cancelSelection)
        self.dlg.attrSelectBox.currentIndexChanged.connect(self.fillBoxFill)

        # GeoRefence System
        pixMap = QPixmap(os.path.join(self.plugin_dir,
                                      'Georeference.svg'))
        geoIcon = QIcon(pixMap)
        self.dlg.geoReferenceBtn.setIcon(geoIcon)
        self.dlg.geoReferenceBtn.setIconSize(0.7*pixMap.rect().size())
        self.dlg.geoReferenceBtn.setToolTip(u'設定參考座標系')
        self.dlg.geoReferenceBtn.clicked.connect(self.selectCrs)

        self.dlg.geoRefBtnInPg4.setIcon(geoIcon)
        self.dlg.geoRefBtnInPg4.setIconSize(0.7*pixMap.rect().size())
        self.dlg.geoRefBtnInPg4.setToolTip(u'設定參考座標系')

        self.dlg.outputMeshPointsBtn.clicked.connect(
            lambda: self.switchAttr('Nodes'))
        self.dlg.outputSegmentsBtn.clicked.connect(
            lambda: self.switchAttr('Segments'))
        self.dlg.outputDistri.clicked.connect(
            lambda: self.switchAttr('Zones'))

        self.dlg.tabWidget.setCurrentIndex(0)
        # Set step2, step3 tab temporary unaccessible
        self.dlg.tabWidget.setTabEnabled(1, False)
        self.dlg.tabWidget.setTabEnabled(2, False)
        self.dlg.outputMeshPointsBtn.setEnabled(False)
        self.dlg.outputSegmentsBtn.setEnabled(False)

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
        wherePolyBtn.pressed.connect(lambda: fileBrowser(self.dlg,
                                                         Caption,
                                                         self.projFolder,
                                                         lineEdit=lineEdit))
        wherePolyBtn.setToolTip(Caption)

        p_Caption = u"請選擇一個點圖層"
        wherePointBtn = self.dlg.wherePointBtn
        p_lineEdit = self.dlg.pointIndicator
        wherePointBtn.pressed.connect(lambda: fileBrowser(self.dlg, p_Caption,
                                                          self.projFolder,
                                                          lineEdit=p_lineEdit))
        wherePointBtn.setToolTip(p_Caption)
        l_Caption = u"請選擇一個線圖層"
        whereLineBtn = self.dlg.whereLineBtn
        l_lineEdit = self.dlg.lineIndicator
        whereLineBtn.pressed.connect(lambda: fileBrowser(self.dlg,
                                                         l_Caption,
                                                         self.projFolder,
                                                         lineEdit=l_lineEdit))
        whereLineBtn.setToolTip(l_Caption)
        g_Caption = u'請選擇GMSH.exe的檔案位置'
        whereGMSH = self.dlg.whereGMSH
        gmshExeEdit = self.dlg.gmshExeEdit
        try:
            path = os.path.dirname(param['GMSH'])
        except:
            path = ''
        gmshExeEdit.setText(param['GMSH'])
        whereGMSH.pressed.connect(lambda: fileBrowser(self.dlg,
                                                      g_Caption, path,
                                                      lineEdit=gmshExeEdit,
                                                      presetType='.exe'))
        whereGMSH.setToolTip(g_Caption)

        loadMshCaption = u'請選擇一個.msh檔案'
        whereMshEdit = self.dlg.whereMshEdit
        whereMshBtn = self.dlg.whereMshBtn
        whereMshBtn.pressed.connect(lambda: fileBrowser(self.dlg,
                                                        loadMshCaption,
                                                        self.getProj(),
                                                        lineEdit=whereMshEdit,
                                                        presetType='.msh'))
        whereMshBtn.setToolTip(loadMshCaption)
        MshLayerCaption = u'請選擇建立讀入網格圖層的資料夾'
        whereMshLayerEdit = self.dlg.whereMshLayerEdit
        whereMshLayerBtn = self.dlg.whereMshLayerBtn
        whereMshLayerBtn.pressed.connect(
            lambda: folderBrowser(self.dlg, MshLayerCaption, self.getProj(),
                                  whereMshLayerEdit))
        whereMshLayerBtn.setToolTip(MshLayerCaption)

        xyzBtn = self.dlg.chooseXyzBtn
        xyzBtn.pressed.connect(self.selectXyz)

        self.dlg.polyConfirm.clicked.connect(
            lambda: self.readLayerChk(self.dlg.polyIndicator, 1))
        self.dlg.pointConfirm.clicked.connect(
            lambda: self.readLayerChk(self.dlg.pointIndicator, 2))
        self.dlg.lineConfirm.clicked.connect(
            lambda: self.readLayerChk(self.dlg.lineIndicator, 3))
        self.dlg.loadMshBtn.clicked.connect(self.loadGeneratedMesh)
        self.dlg.interpExecBtn.clicked.connect(self.mshInterp)

        self.dlg.to2dmExecBtn.clicked.connect(self.to2dmExec)
        self.dlg.backButton.pressed.connect(self.backSwitch)
        self.dlg.backButton.setEnabled(False)

        distCaption = u'請選擇輸出網格檔案的名稱及位置'
        self.dlg.newDistWhere.pressed.connect(
            lambda: saveFileBrowser(self.dlg, distCaption, self.getProj(),
                                    self.dlg.newDistEdit, '(*.msh)'))
        self.dlg.newDistOutput.pressed.connect(self.outputMsh)
        self.dlg.newDistWhere.setToolTip(distCaption)

        self.dlg.new2dmOutput.pressed.connect(self.changeTo2dm)
        self.dlg.outputDistri.setEnabled(False)

        self.dlg.mshPreViewBtn.clicked.connect(self.mshpreview)
        self.dlg.mshPreviewBar.setValue(0)
        self.dlg.mshPreViewBtn.setEnabled(False)
        self.dlg.to2dmExecBtn.setEnabled(False)
        self.dlg.geoRefBtnInPg4.clicked.connect(self.selectCrs)

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

        dirPath = os.path.dirname(__file__)
        main_Icon = os.path.join(dirPath, 'SRH-2D-01.png')
        pre_Icon = os.path.join(dirPath, 'SRHPRP UI-1-01.png')
        viewer_Icon = os.path.join(dirPath, '2DM-VIEWER-01.png')
        flip_Icon = os.path.join(dirPath, 'FLIP LINE-01.png')
        paraview_icon = os.path.join(dirPath, 'PARAVIEW-01.png')
        self.meshAction = self.add_action(
                            main_Icon,
                            text=self.tr(u'Build Mesh For SRH2D'),
                            callback=self.run,
                            parent=self.iface.mainWindow())
        self.srhpredAction = self.add_action(
                            pre_Icon,
                            text=self.tr(u'srhpre UI'),
                            callback=self.srhpre.run,
                            parent=self.iface.mainWindow())
        self.mesh2DViewerAction = self.add_action(
                            viewer_Icon,
                            text=self.tr(u'2dm File Viewer'),
                            callback=self.mesh2D.run,
                            parent=self.iface.mainWindow())
        self.flipAction = self.add_action(
                            flip_Icon,
                            text=self.tr(u'Flip Line'),
                            callback=flip,
                            parent=self.iface.mainWindow())
        self.paraViewAction = self.add_action(
                                paraview_icon,
                                text=self.tr(u'ParaView'),
                                callback=loadParaView,
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

    def cleanProjFolder(self, projFolder):
        # projFolder.replace("\\", "/")
        files = os.listdir(projFolder)
        for name in files:
            if os.path.isfile(os.path.join(projFolder, name)):
                try:
                    os.remove(os.path.join(projFolder, name))
                except:
                    try:
                        subprocess.call(['cmd', '/c', 'del',
                                         os.path.join(projFolder, name)])
                    except:
                        pass

        if os.path.isdir(os.path.join(projFolder, 'MainLayers')):
            try:
                files = rmtree(os.path.join(projFolder, 'MainLayers'))
                os.system('mkdir ' + os.path.join(projFolder, 'MainLayers'))
            except:
                try:
                    subprocess.call(['cmd', '/c', 'RD', '/S', '/Q',
                                     os.path.join(projFolder, 'MainLayers')])
                    subprocess.call(['cmd', '/c', 'mkdir ',
                                     os.path.join(projFolder, 'MainLayers')])
                except:
                    pass
        else:
            os.mkdir(os.path.join(projFolder, 'MainLayers'))

        if os.path.isdir(os.path.join(projFolder, 'InnerLayers')):
            try:
                files = rmtree(os.path.join(projFolder, 'InnerLayers'))
                os.system('mkdir ' + os.path.join(projFolder, 'InnerLayers'))
                # os.mkdir(os.path.join(projFolder, 'InnerLayers'))
            except:
                try:
                    subprocess.call(['cmd', '/c', 'RD', '/S', '/Q',
                                     os.path.join(projFolder, 'InnerLayers')])
                    subprocess.call(['cmd', '/c', 'mkdir ',
                                     os.path.join(projFolder, 'InnerLayers')])
                    # os.mkdir(os.path.join(projFolder, 'InnerLayers'))
                except:
                    pass
        else:
            os.mkdir(os.path.join(projFolder, 'InnerLayers'))

        if os.path.isdir(os.path.join(projFolder, 'MeshShp')):
            try:
                rmtree(os.path.join(projFolder, 'MeshShp'))
                os.system('mkdir ' + os.path.join(projFolder, 'MeshShp'))
                # os.mkdir(os.path.join(projFolder, 'MeshShp'))
            except:
                try:
                    subprocess.call(['cmd', '/c', 'RD', '/S/', '/Q',
                                     os.path.join(projFolder, 'MeshShp')])
                    subprocess.call(['cmd', '/c', 'mkdir',
                                     os.path.join(projFolder, 'MeshShp')])
                    # os.mkdir(os.path.join(projFolder, 'MeshShp'))
                except:
                    pass
        else:
            os.mkdir(os.path.join(projFolder, 'MeshShp'))

    def mshpreview(self):
        proj_Name = os.path.basename(self.projFolder)
        Path = os.path.join(self.projFolder, proj_Name+'.msh')
        outDir = os.path.join(self.projFolder, 'MeshShp', 'preview')
        if not os.path.isdir(outDir):
            os.mkdir(outDir)
        else:
            rmtree(outDir)
            os.mkdir(outDir)

        mshPreview(Path, self.systemCRS, outDir, self.dlg)

    def step1_1(self):
        projFolder = self.dlg.lineEdit.text().encode('big5')
        self.projFolder = projFolder
        self.cleanProjFolder(projFolder)

        layers = self.iface.legendInterface().layers()

        try:
            self.systemCRS
        except(AttributeError):
            crs = QgsCoordinateReferenceSystem(
                3826, QgsCoordinateReferenceSystem.EpsgCrsId)
            self.systemCRS = crs

        MainName = self.dlg.comboBox.currentText()
        if MainName:
            for layer in layers:
                if layer.name() == MainName:
                    mainLayerSelected = layer

            newMainLayer = newPointLayer.copyMainLayer(mainLayerSelected,
                                                       self.systemCRS,
                                                       projFolder)
            source = newMainLayer.source()
            self.iface.mapCanvas().setDestinationCrs(self.systemCRS)
            if newMainLayer:
                self.mainLayer = newMainLayer
            else:
                self.mainLayer = mainLayerSelected

            mainLayerId = QgsMapLayerRegistry.instance().addMapLayer(
                self.mainLayer)
            self.mainLayerId = mainLayerId.id()

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
            innerLayers = innerLayersExport(projFolder, self.mainLayer)
            innerLayers.innerLayers = innerLayersList
            innerLayers.copyLayers()
        else:
            if innerLayersList:
                onCritical(100)

        self.dlg.tabWidget.setTabEnabled(1, True)
        self.dlg.tabWidget.setCurrentIndex(1)
        self.dlg.nextBtn2.setEnabled(False)
        self.step2(source)

    def step1(self):
        layers = self.iface.legendInterface().layers()
        self.dlg.comboBox.clear()

        layerList = list()
        innerLayerList = list()
        for layer in layers:
            innerLayerList.append(layer.name())
            try:
                if layer.geometryType() > 1:
                    layerList.append(layer.name())
            except:
                pass
        self.dlg.comboBox.addItems(layerList)

        self.dlg.listWidget.clear()

        for name in innerLayerList:
            item = QListWidgetItem(name, self.dlg.listWidget)
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            item.setCheckState(Qt.Unchecked)

        try:
            self.dlg.nextBtn1.pressed.disconnect()
            self.dlg.nextBtn1.pressed.connect(self.chkSwitch)
        except:
            self.dlg.nextBtn1.pressed.connect(self.chkSwitch)

    def chkSwitch(self):
        if not self.dlg.lineEdit.text():
            onCritical(101)
        elif not os.path.isdir(self.dlg.lineEdit.text()):
            onCritical(102)
        else:
            folderStr = self.dlg.lineEdit.text().encode('big5')
            self.__parameter__['projFolder'] = folderStr
            self.step1_1()
        self.dlg.__parameter__ = self.__parameter__

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
        layer = self.iface.activeLayer()
        layer.select(selectedFeatures)

    def cancelSelection(self):
        layer = self.iface.mapCanvas().currentLayer()
        layer.removeSelection()

        # WRA 當更改儲存中內容之後，直接把寫入的內容儲存至圖層資料庫
        # self.writeTableToLayer()

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
        layer = self.iface.activeLayer()
        selectedIds = layer.selectedFeaturesIds()
        columns = self.dlg.tableWidget.columnCount()
        table = self.dlg.tableWidget

        for fid in selectedIds:
            for j in range(0, columns):
                item = table.item(fid, j)
                if item:
                    item.setSelected(True)

    def writeTableToLayer(self):
        layer = self.iface.activeLayer()

        fieldDict = self.fieldDict
        layerFields = layer.pendingFields()

        Rows = self.dlg.tableWidget.rowCount()
        Columns = self.dlg.tableWidget.columnCount()

        layer.startEditing()

        for i in range(0, Rows):
            for j in range(0, Columns):
                dat = ""
                item = self.dlg.tableWidget.cellWidget(i, j)
                if item is None:
                    if self.dlg.tableWidget.item(i, j) is not None:
                        dat = self.dlg.tableWidget.item(i, j).text()
                elif isinstance(item, type(QComboBox())):
                    dat = item.currentText()
                elif isinstance(item, type(QLineEdit())):
                    dat = self.dlg.tableWidget.cellWidget(i, j).text()

                try:
                    fieldName = fieldDict[j]
                    idx = layerFields.fieldNameIndex(fieldName)
                except:
                    idx = None
                #
                # From the data type of layer attribute table, change the
                # text in data table to the same type of attribute field,
                # then fill in the attribute table.
                #
                if idx:
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
        self.iface.messageBar().pushMessage('Data in meshBuilder table wrote \
into layer attributes.', level=QgsMessageBar.INFO)
        layer.reload()

    def setTableToPoly(self, layer):
        def setTableItem(i, j, Object, Type='Object', prefix=0):
            if type(Object) != QPyNullVariant and Type == 'Object':
                Object = str(Object)
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(Object))
            elif Type == 'ComboBox':
                widget = QComboBox()
                widget.addItem(u'是')
                widget.addItem(u'否')
                if Object == 1:
                    widget.setCurrentIndex(0)
                elif prefix != 0:
                    widget.setCurrentIndex(prefix)
                else:
                    widget.setCurrentIndex(0)
                self.dlg.tableWidget.setCellWidget(i, j, widget)
            else:
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(""))
        registry = QgsMapLayerRegistry.instance()
        vl = registry.mapLayer(self.mainLayerId)
        self.iface.setActiveLayer(vl)

        self.dlg.tableWidget.clear()
        self.dlg.attrSelectBox.clear()

        self.dlg.tableWidget.setRowCount(layer.featureCount())
        self.dlg.tableWidget.setColumnCount(6)
        self.dlg.tableWidget.setHorizontalHeaderLabels([u'網格間距',
                                                        u'符合邊界',
                                                        u'區域分類',
                                                        u'輸出名',
                                                        u'合併三角網格',
                                                        u'結構化網格'])
        counter = 0
        for feature in layer.getFeatures():
            setTableItem(counter, 0, feature['mesh_size'])
            setTableItem(counter, 1, feature['ForceBound'], Type='ComboBox',
                         prefix=1)
            setTableItem(counter, 2, feature['Physical'])
            setTableItem(counter, 3, feature['geoName'])
            setTableItem(counter, 4, feature['Recombine'], Type='ComboBox')
            setTableItem(counter, 5, feature['Transfinit'], Type='ComboBox',
                         prefix=1)
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
                                         u'合併三角網格',
                                         u'結構化網格'])
        self.tableAttrNameDict = {u'網格間距': 0,
                                  u'符合邊界': 1,
                                  u'區域分類': 2,
                                  u'輸出名': 3,
                                  u'合併三角網格': 4,
                                  u'結構化網格': 5}
        layer = self.iface.activeLayer()
        layer.selectionChanged.connect(self.selectFromQgis)

    def setTableToPoint(self, layer):
        def setTableItem(i, j, Object, Type='Object', prefix=0):
            if type(Object) != QPyNullVariant and Type == 'Object':
                Object = str(Object)
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(Object))
            elif Type == 'ComboBox':
                widget = QComboBox()
                widget.addItem(u'是')
                widget.addItem(u'否')
                if Object == 1:
                    widget.setCurrentIndex(0)
                elif prefix != 0:
                    widget.setCurrentIndex(prefix)
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
        vl = registry.mapLayer(self.pointLayerId)
        self.iface.setActiveLayer(vl)

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
            setTableItem(counter, 2, feature['mesh_size'], Type='Object')
            setTableItem(counter, 3, feature['Physical'])
            setTableItem(counter, 4, feature['geoName'])
            setTableItem(counter, 5, feature['breakPoint'], Type='ComboBox',
                         prefix=1)
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
        layer = self.iface.activeLayer()
        layer.selectionChanged.connect(self.selectFromQgis)

    def setTableToLine(self, layer):
        def setTableItem(i, j, Object, Type='Object', prefix='0'):
            if type(Object) != QPyNullVariant and Type == 'Object':
                Object = str(Object)
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(Object))
            elif Type == 'ComboBox':
                widget = QComboBox()
                widget.addItem(u'是')
                widget.addItem(u'否')
                if Object == 1:
                    widget.setCurrentIndex(0)
                elif prefix != 0:
                    widget.setCurrentIndex(prefix)
                else:
                    widget.setCurrentIndex(0)
                self.dlg.tableWidget.setCellWidget(i, j, widget)
            elif Type == 'ComboBox2':
                widget = QComboBox()
                for k in range(0, len(boundaryOrder)):
                    widget.addItem(str(k+1))
                physName = self.dlg.tableWidget.item(i, 1).text()
                try:
                    idx = boundaryOrder.index(physName)
                except(ValueError):
                    boundaryOrder.append(physName)
                    idx = boundaryOrder.index(physName)
                widget.setCurrentIndex(idx)
                self.dlg.tableWidget.setCellWidget(i, j, widget)
                cell = self.dlg.tableWidget.cellWidget(i, j)
                cell.currentIndexChanged.connect(lambda:
                                                 self.linePhysSeqChanged(1, 2))
            elif type(Object) != QPyNullVariant and Type == 'Fixed':
                Object = str(Object)
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(Object))
                item = self.dlg.tableWidget.item(i, j)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            elif Type == 'Object2':
                widget = QLineEdit()
                if type(Object) != QPyNullVariant:
                    Object = str(Object)
                    widget.setText(Object)

                self.dlg.tableWidget.setCellWidget(i, j, widget)
                widget.textChanged.connect(self.setRefLength)
            else:
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(""))

        try:
            boundaryOrder = self.boundaryOrder
        except:
            boundaryOrder = countPhysics(self.lineLayer)
            self.boundaryOrder = boundaryOrder

        registry = QgsMapLayerRegistry.instance()
        vl = registry.mapLayer(self.lineLayerId)
        self.iface.setActiveLayer(vl)

        self.dlg.tableWidget.clear()
        self.dlg.attrSelectBox.clear()

        self.dlg.tableWidget.setRowCount(0)
        self.dlg.tableWidget.setRowCount(layer.featureCount())
        self.dlg.tableWidget.setColumnCount(7)
        self.dlg.tableWidget.setHorizontalHeaderLabels([u'符合邊界',
                                                        u'邊界性質',
                                                        u'邊界輸出序',
                                                        u'輸出名',
                                                        u'結構化',
                                                        u'切分數量',
                                                        u'參考長度'])
        counter = 0
        for feature in layer.getFeatures():
            setTableItem(counter, 0, feature['ForceBound'], Type='ComboBox',
                         prefix=1)
            setTableItem(counter, 1, feature['Physical'])
            if feature['Physical']:
                setTableItem(counter, 2, self.tr(u''), Type='ComboBox2')
            setTableItem(counter, 3, feature['geoName'])
            setTableItem(counter, 4, feature['Transfinit'], Type='ComboBox',
                         prefix=1)
            setTableItem(counter, 5, feature['Cells'], Type='Object2')
            counter = counter + 1

        fieldDict = {0: 'ForceBound',
                     1: 'Physical',
                     2: 'seq',
                     3: 'geoName',
                     4: 'Transfinit',
                     5: 'Cells'}

        self.fieldDict = fieldDict
        self.currentLayer = layer
        self.dlg.attrSelectBox.addItems([u'符合邊界',
                                         u'邊界性質',
                                         u'輸出名',
                                         u'結構化',
                                         u'切分數量'])
        self.tableAttrNameDict = {u'符合邊界': 0,
                                  u'邊界性質': 1,
                                  u'邊界輸出序': 2,
                                  u'輸出名': 3,
                                  u'結構化': 4,
                                  u'切分數量': 5,
                                  u'參考長度': 6}

        for i in range(0, self.dlg.tableWidget.rowCount()):
            item = QTableWidgetItem()
            if self.dlg.tableWidget.cellWidget(i, 4):
                if (self.dlg.tableWidget.cellWidget(i,
                                                    4).currentIndex() == 0 and
                        self.dlg.tableWidget.cellWidget(i, 5).text()):
                    self.lineLayer.setSelectedFeatures([i])
                    feature = self.lineLayer.selectedFeatures()[0]
                    length = feature.geometry().length()
                    try:
                        n = int(self.dlg.tableWidget.cellWidget(i, 5).text())
                        item.setText(str(length/(n-1)))
                    except:
                        item.setText('')
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.dlg.tableWidget.setItem(i, 6, item)

        layer = self.iface.activeLayer()
        layer.selectionChanged.connect(self.selectFromQgis)
        self.dlg.tableWidget.itemChanged.connect(lambda:
                                                 self.arrangeLineTable(1, 2))

    def zoneLayerStyle(self, layerId):
        registry = QgsMapLayerRegistry.instance()
        layer = registry.mapLayer(layerId)
        style_rules = list()

        for zone in self.regionOrder:
            color_code = randColor()
            style_rules.append((zone, '"Zone"='+"'"+zone+"'", color_code))
        symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
        renderer = QgsRuleBasedRendererV2(symbol)
        root_rule = renderer.rootRule()

        for label, expression, color_name in style_rules:
            rule = root_rule.children()[0].clone()
            rule.setLabel(label)
            rule.setFilterExpression(expression)
            rule.symbol().setColor(QColor(color_name))
            root_rule.appendChild(rule)

        root_rule.removeChildAt(0)
        layer.setRendererV2(renderer)
        layer.triggerRepaint()

    def segLayerStyle(self, layerId):
        registry = QgsMapLayerRegistry.instance()
        layer = registry.mapLayer(layerId)
        style_rules = list()

        for border in self.boundaryOrder:
            color_code = randColor()
            style_rules.append((border, '"Physical"=' + "'" + border + "'",
                                color_code, 0.66))
        color_code = randColor()
        style_rules.append(('Segements', '"Physical" is NULL', color_code,
                            0.26))
        symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
        renderer = QgsRuleBasedRendererV2(symbol)
        root_rule = renderer.rootRule()

        for label, expression, color_name, width in style_rules:
            rule = root_rule.children()[0].clone()
            rule.setLabel(label)
            rule.setFilterExpression(expression)
            rule.symbol().setColor(QColor(color_name))
            rule.symbol().setWidth(width)
            root_rule.appendChild(rule)

        root_rule.removeChildAt(0)
        layer.setRendererV2(renderer)
        layer.triggerRepaint()

    def linePhysSeqChanged(self, nameCol, comCol, push=True):
        boundaryOrder = self.boundaryOrder

        c_row = self.dlg.tableWidget.currentRow()
        c_column = self.dlg.tableWidget.currentColumn()

        table = self.dlg.tableWidget
        try:
            newSeq = table.cellWidget(c_row, c_column).currentIndex()
            physName = table.item(c_row, nameCol).text()

            # Replace the boundary order in boundaries list to the new position.
            oldSeq = boundaryOrder.index(physName)
            boundaryOrder.pop(oldSeq)
            boundaryOrder.insert(newSeq, physName)
            if push:
                msg = ''
                for i in range(0, len(boundaryOrder)):
                    msg = msg + ", " + boundaryOrder[i]
                msg = msg[1:-1]
                self.iface.messageBar().pushMessage(msg)

            for i in range(0, table.rowCount()):
                if table.item(i, nameCol):
                    name = table.item(i, nameCol).text()
                    try:
                        idx = boundaryOrder.index(name)
                        table.cellWidget(i, comCol).setCurrentIndex(idx)
                    except:
                        pass
                elif table.item(i, nameCol).text() == physName:
                    idx = boundaryOrder.index(physName)
                    table.cellWidget(i, comCol).setCurrentIndex(idx)
        except:
            pass
        self.boundaryOrder = boundaryOrder

    def regionOrderChanged(self):
        regionOrder = self.regionOrder
        c_column = self.dlg.tableWidget.currentColumn()

        table = self.dlg.tableWidget

        if c_column == 2:
            iterator = zoneSeqIterator(self.iface, regionOrder, self.dlg)
            res = iterator.run()
            if res == 1:
                table.itemChanged.disconnect()
                rows = table.rowCount()
                self.regionOrder = iterator.zoneOrd
                ordDict = dict()
                for j in range(0, len(self.regionOrder)):
                    ordDict.update({self.regionOrder[j]: j+1})
                for i in range(0, rows):
                    physName = str(table.item(i, 1).text())
                    idx = ordDict[physName]
                    table.setItem(i, 2, QTableWidgetItem(str(idx)))
                table.itemChanged.connect(self.checkLayerRegions)
        else:
            pass

    def arrangeLineTable(self, nameCol, comCol):
        boundaryOrder = self.boundaryOrder
        table = self.dlg.tableWidget
        Boundaries = list()
        for i in range(0, table.rowCount()):
            if table.item(i, nameCol):
                if table.item(i, nameCol).text():
                    Boundaries.append(table.item(i, nameCol).text())
            elif not table.item(i, 1) and table.cellWidget(i, comCol):
                table.removeCellWidget(i, comCol)

        Boundaries = set(Boundaries)
        Boundaries = list(Boundaries)

        for m in range(0, len(Boundaries)):
            if not Boundaries[m] in boundaryOrder:
                boundaryOrder.append(Boundaries[m])

        popIdx = list()
        for k in range(0, len(boundaryOrder)):
            if not boundaryOrder[k] in Boundaries:
                popIdx.append(k)
        if popIdx:
            boundaryOrder = [i for j,
                             i in enumerate(boundaryOrder) if j not in popIdx]

        for i in range(0, table.rowCount()):
            if table.item(i, nameCol):
                if table.item(i, nameCol).text():
                    name = table.item(i, nameCol).text()
                    idx = boundaryOrder.index(name)
                    if not table.cellWidget(i, comCol):
                        widget = QComboBox()
                        for k in range(0, len(boundaryOrder)):
                            widget.addItem(str(k+1))
                        widget.setCurrentIndex(boundaryOrder.index(name))
                        table.setCellWidget(i, comCol, widget)
                        widget.currentIndexChanged.connect(
                            lambda: self.linePhysSeqChanged(nameCol, comCol))
                    else:
                        wigItems = table.cellWidget(i, comCol).count()
                        if wigItems < len(boundaryOrder):
                            table.cellWidget(i, comCol).setMaxCount(
                                len(boundaryOrder))
                            for z in range(wigItems, len(boundaryOrder)):
                                table.cellWidget(i, comCol).addItem(str(z+1))
                            for f in range(0, len(boundaryOrder)):
                                table.cellWidget(i, comCol).setItemText(
                                    f, str(f+1))
                        elif wigItems > len(boundaryOrder):
                            num = table.cellWidget(i, comCol).count()
                            while num > len(boundaryOrder):
                                table.cellWidget(i, comCol).removeItem(0)
                                num = table.cellWidget(i, comCol).count()
                            for f in range(0, table.cellWidget(i,
                                                               comCol).count()):
                                table.cellWidget(i, comCol).setItemText(
                                    f, str(f+1))

                    table.cellWidget(i, comCol).setCurrentIndex(idx)
            else:
                if table.cellWidget(i, comCol):
                    table.removeCellWidget(i, comCol)
        self.boundaryOrder = boundaryOrder

    def setRefLength(self):
        table = self.dlg.tableWidget

        for i in range(0, table.rowCount()):
            try:
                if (table.cellWidget(i, 4).currentIndex() == 0 and
                        table.cellWidget(i, 5).text()):
                    self.lineLayer.setSelectedFeatures([i])
                    feature = self.lineLayer.selectedFeatures()[0]
                    length = feature.geometry().length()
                    try:
                        n = int(table.cellWidget(i, 5).text())
                        table.item(i, 6).setText(str(length/(n-1)))
                    except:
                        table.item(i, 6).setText('')
            except:
                pass

    def segPhysOrdChanged(self):
        physDict = self.linePhysSeq
        physList = dictToList(physDict)

        c_row = self.dlg.tableWidget.currentRow()
        c_column = self.dlg.tableWidget.currentColumn()

        table = self.dlg.tableWidget

        newSeq = table.cellWidget(c_row, c_column).currentIndex()
        physName = table.item(c_row, 0).text()
        for i in range(0, table.rowCount()):
            if table.item(i, 0).text() == physName:
                table.cellWidget(i, 1).setCurrentIndex(newSeq)

        oldSeq = physDict[physName]
        if newSeq > oldSeq:
            physList.insert(newSeq+1, physName)
            physList.pop(oldSeq)
        elif newSeq <= oldSeq:
            physList.insert(newSeq, physName)
            physList.pop(oldSeq+1)

        phySeq_dict = makeDict(physList)

        for j in range(0, table.rowCount()):
            if table.item(j, 0).text() and table.cellWidget(j, 1):
                try:
                    name = table.item(j, 0).text()
                    table.cellWidget(j, 1).setCurrentIndex(phySeq_dict[name])
                except:
                    pass
        self.linePhysSeq = phySeq_dict

    def setTableToNodes(self, layer):
        def setTableItem(i, j, Object, Type='Object'):
            if type(Object) != QPyNullVariant and Type == 'Object':
                Object = str(Object)
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(Object))
            elif Type == 'ComboBox':
                widget = QComboBox()
                widget.addItem(u'是')
                widget.addItem(u'否')
                if Object == 1:
                    widget.setCurrentIndex(0)
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
        vl = registry.mapLayer(self.nodeLayerId)
        self.iface.setActiveLayer(vl)

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
        #  Connect QGIS active layer to table, if selection is made in QGIS
        #  interface, reflect the selection result to data table.
        layer = self.iface.activeLayer()
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
                if Object == 1:
                    widget.setCurrentIndex(0)
                else:
                    widget.setCurrentIndex(0)
                self.dlg.tableWidget.setCellWidget(i, j, widget)
            elif Type == 'ComboBox2':
                widget = QComboBox()
                for k in range(0, len(boundaryOrder)):
                    widget.addItem(str(k+1))
                name = self.dlg.tableWidget.item(i, 0).text()
                idx = boundaryOrder.index(name)
                widget.setCurrentIndex(idx)
                self.dlg.tableWidget.setCellWidget(i, j, widget)
                cell = self.dlg.tableWidget.cellWidget(i, j)
                cell.currentIndexChanged.connect(
                    lambda: self.linePhysSeqChanged(0, 1, False))
            elif type(Object) != QPyNullVariant and Type == 'Fixed':
                Object = str(Object)
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(Object))
                item = self.dlg.tableWidget.item(i, j)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            else:
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(""))
        registry = QgsMapLayerRegistry.instance()
        vl = registry.mapLayer(self.segLayerId)
        self.iface.setActiveLayer(vl)

        if len(self.boundaryOrder) == 0:
            meshFile = self.dlg.whereMshEdit.text()
            self.boundaryOrder, self.regionOrder = loadMshBoundaries(meshFile)
            boundaryOrder = self.boundaryOrder
        else:
            boundaryOrder = self.boundaryOrder

        self.dlg.tableWidget.clear()
        self.dlg.attrSelectBox.clear()

        self.dlg.tableWidget.setRowCount(layer.featureCount())
        self.dlg.tableWidget.setColumnCount(2)
        self.dlg.tableWidget.setHorizontalHeaderLabels([u'邊界性質',
                                                        u'邊界輸出序'])
        counter = 0

        for feature in layer.getFeatures():
            setTableItem(counter, 0, feature['Physical'])
            if feature['Physical']:
                setTableItem(counter, 1, self.tr(u''), Type='ComboBox2')
            counter = counter + 1

        fieldDict = {0: 'Physical',
                     1: 'seq'}

        self.fieldDict = fieldDict
        self.currentLayer = layer
        self.dlg.attrSelectBox.addItems([u'邊界性質'])
        self.tableAttrNameDict = {u'邊界性質': 0,
                                  u'邊界輸出序': 1}

        layer = self.iface.activeLayer()
        layer.selectionChanged.connect(self.selectFromQgis)
        self.dlg.tableWidget.itemChanged.connect(lambda:
                                                 self.arrangeLineTable(0, 1))
        self.segLayerStyle(self.segLayerId)

    def setTableToZone(self, zoneLayer):
        def setTableItem(i, j, Object, Type='Object'):
            if type(Object) != QPyNullVariant and Type == 'Object':
                Object = str(Object)
                self.dlg.tableWidget.setItem(i, j, QTableWidgetItem(Object))
            elif Type == 'ComboBox':
                widget = QComboBox()
                widget.addItem(u'是')
                widget.addItem(u'否')
                if Object == 1:
                    widget.setCurrentIndex(0)
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
        vl = registry.mapLayer(self.zoneLayerId)
        self.iface.setActiveLayer(vl)

        regionOrder = self.regionOrder
        self.iface.messageBar().pushMessage(str(regionOrder))

        self.dlg.tableWidget.clear()
        self.dlg.attrSelectBox.clear()

        self.dlg.tableWidget.setRowCount(zoneLayer.featureCount())
        self.dlg.tableWidget.setColumnCount(3)

        self.dlg.tableWidget.setHorizontalHeaderLabels([u'id', u'區域分類',
                                                        u'輸出序'])

        counter = 0
        for feature in zoneLayer.getFeatures():
            setTableItem(counter, 0, str(feature['id']), Type='Fixed')
            setTableItem(counter, 1, feature['Zone'])

            try:
                setTableItem(counter, 2,
                             str(regionOrder.index(feature['Zone'])+1))
            except:
                self.regionOrder = zoneFromLayer(self.zoneLayer)
            counter += 1

        fieldDict = {0: 'id',
                     1: 'Zone'}

        self.fieldDict = fieldDict
        self.currentLayer = zoneLayer
        self.dlg.attrSelectBox.addItems([u'區域分類'])
        self.tableAttrNameDict = {u'區域分類': 1}
        #  Connect QGIS active layer to table, if selection is made in QGIS
        #  interface, reflect the selection result to data table.
        layer = self.iface.activeLayer()
        layer.selectionChanged.connect(self.selectFromQgis)

        self.zoneLayerStyle(self.zoneLayerId)
        self.dlg.tableWidget.itemChanged.connect(self.checkLayerRegions)
        self.dlg.tableWidget.itemClicked.connect(self.regionOrderChanged)

    def checkLayerRegions(self):
        table = self.dlg.tableWidget
        regionOrder = self.regionOrder

        regions = list()
        for i in range(0, table.rowCount()):
            regions.append(table.item(i, 1).text())
        regionsSet = set(regions)
        for item in regionsSet:
            if item not in regionOrder:
                regionOrder.append(item)
        for item in regionOrder:
            if item not in regionsSet:
                idx = regionOrder.index(item)
                regionOrder.pop(idx)
        self.regionOrder = regionOrder

        for i in range(0, table.rowCount()):
            ordItem = table.item(i, 2)

            name = table.item(i, 1).text()
            idx = regionOrder.index(name)
            ordItem.setText(str(idx+1))

        self.zoneLayerStyle()

    def attrTable(self, layer, Type='poly'):
        self.dlg.tableWidget.setRowCount(layer.featureCount())

        if Type == 'poly':
            self.setTableToPoly(layer)
        elif Type == 'point':
            self.setTableToPoint(layer)
        elif Type == 'line':
            self.setTableToLine(layer)

    def switchAttr(self, Type):
        try:
            self.dlg.tableWidget.itemChanged.disconnect()
            self.dlg.tableWidget.itemClicked.disconnect()
            layer = self.iface.activeLayer()
            layer.selectionChanged.disconnect()
        except:
            pass
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
        elif Type == 'Zones':
            self.setTableToZone(self.zoneLayer)

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
            onCritical(102)
        else:
            if switch == 1:
                self.readPolyLayer()
            elif switch == 2:
                self.readPointLayer()
            elif switch == 3:
                self.readLineLayer()

    def readPolyLayer(self):
        path = self.dlg.polyIndicator.text()
        layer = self.iface.addVectorLayer(path, QFileInfo(path).baseName(),
                                          'ogr')
        self.iface.setActiveLayer(layer)

        self.dlg.polyConfirm.setEnabled(False)
        self.mainLayer = layer
        self.systemCRS = self.mainLayer.dataProvider().crs()
        self.attrTable(layer, Type='poly')
        self.dlg.polyAttrBtn.setEnabled(True)
        self.currentProcess = 1

    def readPointLayer(self):
        path = self.dlg.pointIndicator.text()
        layer = self.iface.addVectorLayer(path, QFileInfo(path).baseName(),
                                          'ogr')
        self.iface.setActiveLayer(layer)

        self.dlg.pointConfirm.setEnabled(False)
        self.pointLayer = layer
        self.attrTable(layer, Type='point')
        self.dlg.pointAttrBtn.setEnabled(True)
        self.currentProcess = 2

    def readLineLayer(self):
        path = self.dlg.lineIndicator.text()
        layer = self.iface.addVectorLayer(path, QFileInfo(path).baseName(),
                                          'ogr')
        self.iface.setActiveLayer(layer)

        self.dlg.lineConfirm.setEnabled(False)
        self.lineLayer = layer
        self.attrTable(layer, Type='line')
        self.dlg.lineAttrBtn.setEnabled(True)
        self.boundaryOrder = countPhysics(self.lineLayer)

        lineFrameObj = lineFrame.lineFrame(self.projFolder,
                                           pointLayer=self.pointLayer,
                                           CRS=self.systemCRS)
        self.lineFrameObj = lineFrameObj
        self.currentProcess = 3
        self.dlg.setCompleteBtn.setText(u'合併線段')

    def batchFill(self):
        try:
            self.dlg.tableWidget.itemChanged.disconnect()
        except:
            pass
        layer = self.iface.activeLayer()
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
                elif type(item) == QLineEdit:
                    item.setText(fillText)
            elif item is None:
                item = self.dlg.tableWidget.item(row, currentAttrIdx)
                if fillText:
                    item.setText(fillText)
                else:
                    item.setText("")

        # Cancel Selection after change. (feature canceled)
        """
        for i in range(0, self.dlg.tableWidget.rowCount()):
            for j in range(0, self.dlg.tableWidget.columnCount()):
                if self.dlg.tableWidget.item(i, j):
                    if self.dlg.tableWidget.item(i, j).isSelected():
                        self.dlg.tableWidget.item(i, j).setSelected(False)
                                                                       """
        if layer.name() == 'Segments':
            self.arrangeLineTable(0, 1)
            self.dlg.tableWidget.itemChanged.connect(
                lambda: self.arrangeLineTable(0, 1))
        elif layer.name() == 'Zones':
            self.checkLayerRegions
            self.dlg.tableWidget.itemChanged.connect(self.checkLayerRegions)

        # WRA 使用批次填入後，直接將填入的內容寫回圖層資料庫
        # self.writeTableToLayer()

    def backSwitch(self):
        process = self.currentProcess
        if process == 4:
            layerList = QgsMapLayerRegistry.instance().mapLayersByName(
                'MainLines_frame')
            idList = list()
            for layer in layerList:
                idList.append(layer.id())
            QgsMapLayerRegistry.instance().removeMapLayers(idList)
            del self.lineLayer
            del self.lineFrameObj
            del self.pointDict
            self.switchAttr(Type='point')

            folderFiles = os.listdir(self.projFolder)
            for fileName in folderFiles:
                if 'MainLines_frame' in fileName:
                    subprocess.Popen(
                        ['del', os.path.join(self.projFolder, 'MainLayers',
                                             fileName)])
            self.step2_2()
        elif process == 3:
            layerList = QgsMapLayerRegistry.instance().mapLayersByName(
                'MainLines_frame')
            idList = list()
            for layer in layerList:
                idList.append(layer.id())
            QgsMapLayerRegistry.instance().removeMapLayers(idList)
            del self.lineLayer
            del self.lineFrameObj
            del self.pointDict

            layerList = QgsMapLayerRegistry.instance().mapLayersByName(
                'MainPoint_frame')
            idList = list()
            for layer in layerList:
                idList.append(layer.id())
            QgsMapLayerRegistry.instance().removeMapLayers(idList)
            del self.pointLayer
            self.switchAttr(Type='poly')
            subprocess.call(['cmd', '/c', 'rm', self.projFolder, 'MainLayers',
                             'MainLines_frame.*'])
            subprocess.call(['cmd', '/c', 'rm', self.projFolder, 'MainLayers',
                             'MainPoint_frame.*'])
            self.step2_1()
            self.dlg.setCompleteBtn.setText(u'圖層設定完成')
            self.dlg.lineIndicator.clear()
            self.dlg.lineAttrBtn.setEnabled(False)
        elif process == 2:
            layerList = QgsMapLayerRegistry.instance().mapLayersByName(
                'MainPoint_frame')
            idList = list()
            for layer in layerList:
                idList.append(layer.id())
            QgsMapLayerRegistry.instance().removeMapLayers(idList)
            del self.pointLayer
            self.switchAttr(Type='poly')
            folderFiles = os.listdir(os.path.join(self.projFolder,
                                                  'MainLayers'))
            for fileName in folderFiles:
                if 'MainPoint_frame' in fileName:
                    try:
                        subprocess.Popen(['del',
                                          os.path.join(self.projFolder,
                                                       'MainLayers', fileName)])
                    except:
                        pass

            self.dlg.pointIndicator.clear()
            self.dlg.pointAttrBtn.setEnabled(False)
            self.currentProcess = 1

    def processSwitch(self):
        process = self.currentProcess
        if process == 1:
            self.writeTableToLayer()
            self.iface.messageBar().pushMessage('Data in table wrote to main \
layer attributes, load point layer...', level=QgsMessageBar.INFO)
            self.step2_1()
            self.dlg.backButton.setEnabled(True)
        elif process == 2:
            self.writeTableToLayer()
            self.iface.messageBar().pushMessage('Data in table wrote to point \
layer, load line layer...', level=QgsMessageBar.INFO)
            self.step2_2()
        elif process == 3:
            self.writeTableToLayer()
            self.pointLayer.reload()
            self.lineFrameObj.frameLayer = self.lineLayer
            self.lineFrameObj.pointFrame = self.pointLayer
            self.lineFrameObj.pointDict = lineFrame.pointRef(self.pointLayer)
            self.boundaryOrder = countPhysics(self.lineLayer)

            lineFrame.lineCombine(self.lineFrameObj)
            self.iface.messageBar().pushMessage('Line segments combined \
according to break point setting in point layer.')
            self.setTableToLine(self.lineLayer)
            # Change layer legend style to arrow
            lLayer = self.iface.activeLayer()
            qmlPath = os.path.join(os.path.dirname(__file__), 'arrow.qml')
            lLayer.loadNamedStyle(qmlPath)
            lLayer.triggerRepaint()
            self.step2_3()
        elif process == 4:
            self.writeTableToLayer()
            self.iface.messageBar().pushMessage('Data in table wrote into line layer\
 attribute table, procced to mesh generation.', level=QgsMessageBar.INFO)

        elif process == 10:
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
            layer = self.iface.activeLayer()
            layer.selectionChanged.connect(self.selectFromQgis)
        except(AttributeError):
            pass

        self.currentProcess = 1

    def step2_1(self):
        fileNames = os.listdir(os.path.join(self.projFolder, 'MainLayers'))
        if ('polygon-line.shp' not in fileNames and
                'polygon-points' not in fileNames):
            self.orgPoint, self.orgLine = newPointLayer.pointAndLine(
                self.mainLayer, self.projFolder)
        pointFrameObj = lineFrame.pointFrame(self.projFolder,
                                             orgPointsLayer=self.orgPoint,
                                             CRS=self.systemCRS)
        pointFrameObj.copyPoint()
        pointFrameObj.openLayer()
        self.pointLayerId = pointFrameObj.showLayer()
        self.pointLayer = pointFrameObj.frameLayer

        registry = QgsMapLayerRegistry.instance()
        vl = registry.mapLayer(self.pointLayerId)
        self.iface.setActiveLayer(vl)

        path = os.path.join(self.projFolder, 'MainLayers',
                            'MainPoint_frame.shp')

        self.attrTable(self.pointLayer, Type='point')
        self.dlg.pointIndicator.setText(path)
        self.dlg.pointAttrBtn.setEnabled(True)
        layer = self.iface.activeLayer()
        layer.selectionChanged.connect(self.selectFromQgis)
        self.currentProcess = 2

    def step2_2(self):
        lineFrameObj = lineFrame.lineFrame(self.projFolder,
                                           orgLinesLayer=self.orgLine,
                                           pointLayer=self.pointLayer,
                                           CRS=self.systemCRS)
        lineFrameObj.copyLines()
        lineFrameObj.openLayer()
        self.lineLayerId = lineFrameObj.showLayer()

        self.lineLayer = lineFrameObj.frameLayer
        self.lineFrameObj = lineFrameObj

        registry = QgsMapLayerRegistry.instance()
        vl = registry.mapLayer(self.lineLayerId)
        self.iface.setActiveLayer(vl)
        path = os.path.join(self.projFolder, 'MainLayers',
                            'MainLines_frame.shp')

        self.attrTable(self.lineLayer, Type='line')
        self.dlg.lineIndicator.setText(path)

        self.dlg.lineAttrBtn.setEnabled(True)
        layer = self.iface.activeLayer()
        layer.selectionChanged.connect(self.selectFromQgis)

        self.pointLayer = lineFrameObj.setBreakPoint()
        self.pointDict = lineFrame.pointRef(self.pointLayer)

        self.currentProcess = 3
        self.dlg.setCompleteBtn.setText(u'合併線段')

    def step2_3(self):
        self.dlg.setCompleteBtn.setText(u'圖層設定完成')
        self.currentProcess = 4
        self.dlg.nextBtn2.setEnabled(True)
        self.dlg.nextBtn2.pressed.connect(self.step3)
        self.iface.messageBar().pushMessage("Please complete boundary settings \
to proceed to mesh generation.", level=QgsMessageBar.INFO)

    def step3(self):
        self.dlg.tabWidget.setTabEnabled(2, True)
        self.dlg.tabWidget.setCurrentIndex(2)

    def outputMsh(self):
        self.writeTableToLayer()
        meshFile = self.dlg.newDistEdit.text()
        meshOutput(meshFile, self.nodeLayer, self.segLayer,
                   self.zoneLayer, self.regionOrder)
        message = u'New mesh data wrote to ' + meshFile
        self.iface.messageBar().pushMessage(message, level=QgsMessageBar.INFO)

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
        GMSH = self.dlg.gmshExeEdit.text().replace(' ', '\ ')
        self.__parameter__['GMSH'] = GMSH
        self.dlg.__parameter__ = self.__parameter__
        proj_Name = os.path.basename(self.projFolder)
        geoPath = os.path.join(self.projFolder, proj_Name+'.geo')
        mshPath = os.path.join(self.projFolder, 'MainLayers',
                               proj_Name+'_gen.msh')

        if not os.path.isdir(os.path.join(self.projFolder, 'MainLayers')):
            os.mkdir(os.path.join(self.projFolder, 'MainLayers'))

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
        P.start(command)

        self.dlg.textBrowser.setText(command)
        self.dlg.Finished = True

    def selectCrs(self):
        crsDiag = QgsGenericProjectionSelector()
        crsDiag.exec_()
        crsId = crsDiag.selectedCrsId()
        crsType = QgsCoordinateReferenceSystem.InternalCrsId
        self.systemCRS = QgsCoordinateReferenceSystem(crsId, crsType)

    def genShpFolder(self, shpFolder):
        if os.path.isdir(os.path.join(self.projFolder, 'MeshShp', shpFolder)):
            folderSplit = re.split('_', shpFolder)
            if len(folderSplit) == 1:
                shpFolder = shpFolder + '_1'
                shpFolder = self.genShpFolder(shpFolder)
                return shpFolder
            else:
                try:
                    _shpFolder = ''
                    for i in range(0, len(folderSplit)-1):
                        _shpFolder += (folderSplit[i] + '_')
                    shpFolder = _shpFolder + str(int(folderSplit[-1])+1)
                    shpFolder = self.genShpFolder(shpFolder)
                    return shpFolder
                except:
                    shpFolder = shpFolder + '_1'
                    shpFolder = self.genShpFolder(shpFolder)
                    return shpFolder
        else:
            return shpFolder

    def loadGeneratedMesh(self):
        def genMesh(meshFile, shpFolder, systemCRS):
            if not os.path.isdir(os.path.join(self.projFolder, 'MeshShp')):
                subprocess.call(['cmd', '/c', 'mkdir',
                                os.path.join(self.projFolder, 'MeshShp')])

            if os.path.isdir(os.path.join(self.projFolder, 'MeshShp',
                                          shpFolder)):
                try:
                    shpFolder = self.genShpFolder(shpFolder)
                    subprocess.call(['cmd', '/c', 'mkdir',
                                     os.path.join(self.projFolder, 'MeshShp',
                                                  shpFolder)])
                except:
                    shpFolder = ''
            else:
                subprocess.call(['cmd', '/c', 'mkdir',
                                os.path.join(self.projFolder, 'MeshShp',
                                             shpFolder)])

            outDir = os.path.join(self.projFolder, 'MeshShp', shpFolder)

            if os.path.isfile(meshFile):
                self.boundaryOrder, self.regionOrder, layerid = loadMesh(
                    meshFile, systemCRS, outDir, self.dlg)
                self.iface.messageBar().pushMessage(str(layerid))

                msg = ''
                for i in range(0, len(self.boundaryOrder)):
                    msg = self.boundaryOrder[i] + ", "
                msg = msg[:-2]
                self.iface.messageBar().pushMessage(msg)

                try:
                    idx = [r for r, j in zip(count(), layerid) if 'Nodes' in j]
                    idx = idx[0]
                    Instance = QgsMapLayerRegistry.instance()
                    NodeLayer = Instance.mapLayer(layerid[idx][1])
                    self.iface.setActiveLayer(NodeLayer)
                    self.nodeLayerId = layerid[idx][1]
                    self.setTableToNodes(NodeLayer)
                    self.nodeLayer = NodeLayer

                    idx = [r for r, j in zip(count(),
                                             layerid) if 'Segments' in j]
                    idx = idx[0]
                    SegmentLayer = Instance.mapLayer(layerid[idx][1])

                    self.segLayerId = layerid[idx][1]
                    self.segLayer = SegmentLayer
                    self.segLayerStyle(self.segLayerId)

                    idx = [r for r, j in zip(count(), layerid) if 'Zones' in j]
                    idx = idx[0]
                    zoneLayer = Instance.mapLayer(layerid[idx][1])
                    self.zoneLayerId = layerid[idx][1]
                    self.zoneLayer = zoneLayer
                    self.zoneLayerStyle(self.zoneLayerId)

                except:
                    if not os.path.isfile(meshFile):
                        onCritical(116)
                    elif not os.path.isdir(outDir):
                        onCritical(117)
            else:
                onCritical(122)

        def loadOld(meshFile, shpFolder):
            Instance = QgsMapLayerRegistry.instance()
            group = QgsProject.instance().layerTreeRoot().addGroup(shpFolder)

            folder = os.path.join(self.projFolder, 'MeshShp', shpFolder)
            self.boundaryOrder, self.regionOrder = loadMshBoundaries(meshFile)

            NodePath = os.path.join(folder, 'Nodes.shp')
            nodelayer = QgsVectorLayer(NodePath, QFileInfo(NodePath).baseName(),
                                       'ogr')
            mNodeLayer = Instance.addMapLayer(nodelayer, False)
            group.addLayer(nodelayer)
            nodelayer.reload()
            SegPath = os.path.join(folder, 'Segments.shp')
            seglayer = QgsVectorLayer(SegPath, QFileInfo(SegPath).baseName(),
                                      'ogr')
            mSegLayer = Instance.addMapLayer(seglayer, False)
            group.addLayer(seglayer)
            seglayer.reload()
            ZonePath = os.path.join(folder, 'Zones.shp')
            zonelayer = QgsVectorLayer(ZonePath, QFileInfo(ZonePath).baseName(),
                                       'ogr')
            mZoneLayer = Instance.addMapLayer(zonelayer, False)
            group.addLayer(zonelayer)
            zonelayer.reload()

            self.boundaryOrder = boundariesFromLayer(seglayer)
            self.regionOrder = zoneFromLayer(zonelayer)

            NodeLayer = Instance.mapLayer(mNodeLayer.id())
            self.iface.setActiveLayer(NodeLayer)
            self.nodeLayerId = mNodeLayer.id()
            self.setTableToNodes(NodeLayer)
            self.nodeLayer = NodeLayer

            SegmentLayer = Instance.mapLayer(mSegLayer.id())
            self.segLayer = SegmentLayer
            self.segLayerStyle(mSegLayer.id())
            self.segLayerId = mSegLayer.id()

            zoneLayer = Instance.mapLayer(mZoneLayer.id())
            self.zoneLayer = zoneLayer
            self.zoneLayerStyle(mZoneLayer.id())
            self.zoneLayerId = mZoneLayer.id()

            size = self.dlg.maximumSize()
            self.dlg.resize(size)
            self.dlg.outputMeshPointsBtn.setEnabled(True)
            self.dlg.outputSegmentsBtn.setEnabled(True)
            self.dlg.outputDistri.setEnabled(True)

        refId = QgsCoordinateReferenceSystem.EpsgCrsId
        if not self.systemCRS:
            systemCRS = QgsCoordinateReferenceSystem(3826, refId)
        else:
            systemCRS = self.systemCRS
        meshFile = self.dlg.whereMshEdit.text()
        shpFolder = os.path.splitext(os.path.basename(meshFile))[0]

        try:
            self.projFolder
        except(AttributeError):
            self.projFolder = self.dlg.whereMshLayerEdit.text()

        loader = loadSelector(self.iface, u'選擇QGIS圖層處理方式')
        result = loader.run()
        if result == 1:
            genMesh(meshFile, shpFolder, systemCRS)
        else:
            loadOld(meshFile, shpFolder)

    def getProj(self):
        try:
            destFolder = self.projFolder
        except(AttributeError):
            destFolder = os.path.expanduser("~")
        return destFolder

    def to2dmExec(self):
        proj_Name = os.path.basename(self.projFolder)
        mshPath = os.path.join(self.projFolder, proj_Name + '.msh')
        folder = os.path.dirname(mshPath)
        fileName = os.path.basename(mshPath).replace('.msh', '.2dm')
        path2dm = os.path.join(folder, fileName)

        ibcName = os.path.basename(path2dm).replace('.2dm', '.ibc')
        dirname = os.path.dirname(path2dm)
        ibcPath = os.path.join(dirname, ibcName)
        mainDir = os.path.dirname(__file__)
        if os.path.isfile(ibcPath):
            subprocess.call(['cmd', '/c', os.path.join(mainDir, "GMSH2SRH.exe"),
                             mshPath, path2dm, ibcPath])
        else:
            subprocess.call(['cmd', '/c', os.path.join(mainDir, "GMSH2SRH.exe"),
                             mshPath, path2dm])
        self.dlg.label_21.setText(u'輸出為' + path2dm)

    def changeTo2dm(self):
        meshFile = self.dlg.newDistEdit.text()
        folder = os.path.dirname(meshFile)
        fileName = os.path.basename(meshFile).replace('.msh', '.2dm')
        path2dm = os.path.join(folder, fileName)

        ibcName = os.path.basename(path2dm).replace('.2dm', '.ibc')
        dirname = os.path.dirname(path2dm)
        ibcPath = os.path.join(dirname, ibcName)
        mainDir = os.path.dirname(__file__)
        if os.path.isfile(ibcPath):
            subprocess.call(['cmd', '/c', os.path.join(mainDir,
                                                       "GMSH2SRH.exe"),
                             meshFile, path2dm, ibcPath])
        else:
            subprocess.call(['cmd', '/c', os.path.join(mainDir,
                                                       "GMSH2SRH.exe"),
                             meshFile, path2dm])
        self.iface.messageBar().pushMessage(".msh Transfomed to .2dm",
                                            level=QgsMessageBar.INFO)
        self.dlg.label_26.setText(u'輸出為' + path2dm)

    def mshInterp(self):
        def writeMsgToLabel(P):
            while P.canReadLine():
                line = u'執行中...' + toUnicode(str(P.readLine())[:-1])
                self.dlg.label_xyz.setText(line)

        def onFinished():
            self.dlg.label_xyz.setText(u'完成')
            self.dlg.whereMshEdit.setText(Path)
            self.dlg.mshPreViewBtn.setEnabled(True)
            self.dlg.to2dmExecBtn.setEnabled(True)

        proj_Name = os.path.basename(self.projFolder)
        Path = os.path.join(self.projFolder, proj_Name+'.msh')
        mshPath = os.path.join(self.projFolder, 'MainLayers',
                               proj_Name + '_gen.msh')

        homeFolder = os.path.dirname(__file__)
        os.chdir(homeFolder)

        P = QProcess()
        P.setProcessChannelMode(QProcess.MergedChannels)
        P.readyReadStandardOutput.connect(lambda: writeMsgToLabel(P))

        env = QProcessEnvironment.systemEnvironment()
        env.remove("TERM")
        P.setProcessEnvironment(env)
        try:
            plugin_dir = os.path.dirname(__file__)
            interpPath = os.path.join(plugin_dir, 'Interpolate',
                                      'ZInterporate.exe')
            command = (interpPath + ' "' + mshPath +
                       '" "' + self.xyzName + '" "' + Path + '"')
            P.start(command)
            self.dlg.label_xyz.setText(u'執行中...')
            P.finished.connect(onFinished)
        except(IOError):
            onCritical(105)

    def dirEmpty(self, directory, lineEdit, lineEditText):
        try:
            files = os.listdir(directory)
            subprocess.Popen(['RD', '/S', '/Q', "mainLayers"])
            subprocess.Popen(['RD', '/S', '/Q', "InnerLayers"])
            if files:
                onWarning(300, lineEdit, lineEditText)
        except(WindowsError, ValueError):
            pass

    def run(self):

        refId = QgsCoordinateReferenceSystem.PostgisCrsId
        self.systemCRS = QgsCoordinateReferenceSystem(3826, refId)

        """Run method that performs all the real work"""

        # show the dialog
        self.dlg.resize(self.dlg.minimumSize())
        # Read current layer in mapLayerRegistry, begin the first step.
        self.step1()

        self.dlg.show()
        # See if OK was pressed

    def selectXyz(self):
        chooseXyzCaption = u'請選擇.xyz或.asc格式之高程檔案'
        self.xyzName = fileBrowser(self.dlg, chooseXyzCaption, self.getProj(),
                                   lineEdit='', presetType='(*.xyz *.asc)')
        self.dlg.label_xyz.setText(u'已選擇DEM檔案')


mshTypeRef = {15: 1, 1: 2, 2: 3, 3: 4, 4: 5}


def loadMshBoundaries(filename):
    meshfile = open(filename, 'r',)
    mesh = meshfile.readlines()
    meshfile.close()

    read = False
    boundaryOrder = list()
    regionOrder = list()
    for l in mesh:
        w = l.split()
        if w[0] == "$PhysicalNames":
            read = True
        if len(w) > 1 and read:
            dim, tag, name = int(w[0]), int(w[1]), w[2]
            name = name[1:-1]
            # Boundaries
            if dim == 1:
                boundaryOrder.append(name)
            elif dim == 2:
                regionOrder.append(name)

        if w[0] == '$EndPhysicalNames':
            break

    return boundaryOrder, regionOrder


def loadMesh(filename, crs, outDir, dlg):
    meshfile = open(filename, 'r')
    meshName = filename.split('/')[-1]
    mesh = meshfile.readlines()
    SegList = dict()
    meshfile.close()

    vertices = dict()
    physicalNames = dict()
    layerPath = dict()
    NodeFeature = dict()
    mode = 0
    endStatements = ["$EndPhysicalNames", "$EndNodes", "$EndElements"]

    fields = QgsFields()
    fields.append(QgsField("id", QVariant.Int))
    nodePath = os.path.join(outDir, "Nodes.shp")
    NodeFields = QgsFields()
    NodeFields.append(QgsField("id", QVariant.Int))
    NodeFields.append(QgsField("Z", QVariant.Double))
    NodeFields.append(QgsField("Physical", QVariant.String))
    NodeWriter = QgsVectorFileWriter(nodePath, "UTF-8", NodeFields,
                                     QGis.WKBPoint, crs, "ESRI Shapefile")
    SegFields = QgsFields()
    SegFields.append(QgsField("id", QVariant.Int))
    SegFields.append(QgsField("Physical", QVariant.String))
    SegFields.append(QgsField("seq", QVariant.Int))
    SegPath = os.path.join(outDir, "Segments.shp")
    SegWriter = QgsVectorFileWriter(SegPath, "UTF-8", SegFields,
                                    QGis.WKBLineString, crs, "ESRI Shapefile")
    del SegWriter
    SegLayer = QgsVectorLayer(SegPath, 'Segments', 'ogr')
    ZoneFields = QgsFields()
    ZoneFields.append(QgsField('id', QVariant.Int))
    ZoneFields.append(QgsField('Zone', QVariant.String))

    zonePath = os.path.join(outDir, 'Zones.shp')
    ZoneWriter = QgsVectorFileWriter(zonePath, "utf-8", ZoneFields,
                                     QGis.WKBPolygon, crs, "ESRI Shapefile")
    del ZoneWriter
    ZoneLayer = QgsVectorLayer(zonePath, 'Zones', 'ogr')
    counter = 0
    boundaryOrder = list()
    regionOrder = list()
    polygonList = list()
    segmentFeatureList = list()
    Seg_idTag = 0
    for l in mesh:
        w = l.split()

        if not w:
            pass
        elif w[0] == "$PhysicalNames":
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

            # Create QGIS layers
            if dim == 1:
                boundaryOrder.append(name)
            elif dim >= 2:
                regionOrder.append(name)

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

                keyString = [int(ElementNodes[0]), int(ElementNodes[1])]
                keyString.sort()

                val = SegList.get(tuple(keyString))
                if val is None:
                    x1, y1, z1 = vertices[int(ElementNodes[0])]
                    x2, y2, z2 = vertices[int(ElementNodes[1])]
                    WktString = ("LINESTRING (" + str(x1) + " " + str(y1) + ",")
                    WktString = WktString + str(x2) + " " + str(y2) + ")"
                    boundName = physicalNames[int(tagArgs[0])][1]
                    SegList.update({(int(ElementNodes[0]),
                                     int(ElementNodes[1])): 0})
                    feature = QgsFeature()
                    feature.setGeometry(QgsGeometry().fromWkt(WktString))
                    seq = boundaryOrder.index(boundName)+1
                    feature.setAttributes([Seg_idTag, boundName, seq])
                    segmentFeatureList.append(feature)
                    Seg_idTag += 1
                    del feature
            elif NodesNum > 2:
                geoString = "POLYGON (("
                ElementNodes.append(ElementNodes[0])
                for pid in ElementNodes:
                    x, y, z = vertices[int(pid)]
                    geoString = geoString + str(x) + " " + str(y) + ","
                geoString = geoString[:-1] + "))"

                zoneFeature = QgsFeature()
                zoneFeature.setFields(ZoneFields)
                zoneFeature.setGeometry(QgsGeometry().fromWkt(geoString))
                zoneFeature.setAttributes(
                    [int(fid), physicalNames[int(tagArgs[0])][1]])

                polygonList.append(zoneFeature)
                del zoneFeature

                for i in range(1, len(ElementNodes)):
                    keyString = [int(ElementNodes[i-1]), int(ElementNodes[i])]
                    keyString.sort()
                    key = SegList.get(tuple(keyString))
                    if key is None:
                        x1, y1, z1 = vertices[int(ElementNodes[i-1])]
                        x2, y2, z2 = vertices[int(ElementNodes[i])]
                        WktString = ("LINESTRING (" + str(x1) + " " + str(y1) +
                                     ",")
                        WktString = WktString + str(x2) + " " + str(y2) + ")"
                        SegList.update({(int(ElementNodes[i-1]),
                                         int(ElementNodes[i])): 0})
                        feature = QgsFeature()
                        feature.setGeometry(QgsGeometry().fromWkt(WktString))
                        feature.setAttributes([Seg_idTag, None, None])
                        segmentFeatureList.append(feature)
                        Seg_idTag += 1
                        del feature

        elif mode == 0:
            continue
        elif len(w) == 1:
            continue
        counter = counter + 1
        dlg.meshLoadProgress.setValue(int(float(counter)/len(mesh)*100))

    currProcess = int(float(counter)/len(mesh)*100)
    imComplete = 100 - int(float(counter)/len(mesh)*100)

    TotalLength = len(NodeFeature.keys()) + len(SegList.keys())
    counter = 0

    for key in NodeFeature.keys():
        feature = QgsFeature()
        geoString = NodeFeature[key][0]
        Z = NodeFeature[key][1]
        phys = NodeFeature[key][2]
        feature.setGeometry(QgsGeometry().fromWkt(geoString))
        feature.setAttributes([key, Z, phys])
        NodeWriter.addFeature(feature)
        counter += 1
        dlg.meshLoadProgress.setValue(
            currProcess + int(counter/TotalLength*imComplete))

    del NodeWriter
    del NodeFeature

    layerPath.update({1: nodePath})

    del SegList
    segEditable = SegLayer.startEditing()
    if segEditable:
        SegLayer.addFeatures(segmentFeatureList)
    SegLayer.commitChanges()

    zoneEditable = ZoneLayer.startEditing()
    if zoneEditable:
        ZoneLayer.addFeatures(polygonList)
    ZoneLayer.commitChanges()

    layerPath.update({2: SegPath})
    layerPath.update({3: zonePath})
    dlg.meshLoadProgress.setValue(100)
    layerid = loadMeshLayers(layerPath, meshName)

    size = dlg.maximumSize()
    dlg.resize(size)
    dlg.pointAttrBtn.setDisabled(True)
    dlg.lineAttrBtn.setDisabled(True)
    dlg.polyAttrBtn.setDisabled(True)
    dlg.setCompleteBtn.setDisabled(True)
    dlg.outputMeshPointsBtn.setEnabled(True)
    dlg.outputSegmentsBtn.setEnabled(True)
    dlg.outputDistri.setEnabled(True)

    return boundaryOrder, regionOrder, layerid


def boundariesFromLayer(SegmentLayer):
    allBoundaries = list()
    for feature in SegmentLayer.getFeatures():
        if feature['Physical']:
            name = feature['Physical']
            seq = feature['seq']
            allBoundaries.append((name, seq))
    allBoundaries = set(allBoundaries)
    allBoundaries = list(allBoundaries)
    allBoundaries = sorted(allBoundaries, key=itemgetter(1))

    boundaryOrder = list()
    for i in range(0, len(allBoundaries)):
        boundaryOrder.append(allBoundaries[i][0])

    return boundaryOrder


def zoneFromLayer(zoneLayer):
    allZones = list()
    for feature in zoneLayer.getFeatures():
        if feature['Zone']:
            allZones.append(feature['Zone'])
    allZones = set(allZones)
    allZones = list(allZones)
    allZones.sort()

    return allZones


def loadMeshLayers(layerPath, meshName):
    meshName.replace('.msh', '')
    group = QgsProject.instance().layerTreeRoot().addGroup(meshName)

    keyString = layerPath.keys()
    keyString.sort()
    layerid = list()
    for key in keyString:
        path = layerPath[key]
        layer = QgsVectorLayer(path, QFileInfo(path).baseName(), 'ogr')
        mlayer = QgsMapLayerRegistry.instance().addMapLayer(layer, False)
        layerid.append([QFileInfo(path).baseName(), mlayer.id()])
        group.addLayer(layer)
        layer.reload()
    return layerid


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


def physSegArrange(physicalSeg, twoEnds):
    def findNext(node):
        for i in range(0, len(physicalSeg)):
            line = physicalSeg[i]
            if line[0] == node:
                return physicalSeg.pop(i)
            elif line[1] == node:
                line = physicalSeg.pop(i)
                newline = list()
                newline.append(line[1])
                newline.append(line[0])
                return newline
    _ArrangedSegs = list()
    for i in range(0, len(physicalSeg)):
        line = physicalSeg[i]
        if line[0] in twoEnds:
            _ArrangedSegs.append(physicalSeg.pop(i))
            break
        elif line[-1] in twoEnds:
            newline = list()
            newline.append(line[-1])
            newline.append(line[0])
            _ArrangedSegs.append(newline)
            physicalSeg.pop(i)
            break

    try:
        startNode = _ArrangedSegs[0][1]
    except:
        f = open('error.txt', 'w')
        for i in range(0, len(physicalSeg)):
            line = str(physicalSeg[i])
            f.write(line+'\n')
        f.close()
    while len(physicalSeg) > 1:
        try:
            line = findNext(startNode)
            _ArrangedSegs.append(line)
            startNode = line[1]
        except(TypeError):
            QgsMessageLog.instance().logMessage('Physical Boundary Break in sin\
gular Node:' + str(startNode))
    _ArrangedSegs.append(physicalSeg.pop(0))

    return _ArrangedSegs


def headAndTail(refList, physicalSeg):
    ArrangedSeg = copy(physicalSeg)
    for key in refList.keys():
        if len(physicalSeg[key]) > 0:
            nodes = refList[key]
            nodes = Counter(nodes)
            #  Find the element only appeared once (Start point and end point)
            terminals = list()
            for node in nodes.keys():
                if nodes[node] == 1:
                    terminals.append(node)

            ArrangedSeg[key] = physSegArrange(physicalSeg[key], terminals)
        else:
            continue
    # f.close()
    return ArrangedSeg


def arangeSegLines(SegLayer, physicsRef, nodeRef):
    physicalLines = list()
    refList = dict()
    _physicalSegs = dict()
    arrangedSegs = dict()
    for key in physicsRef.keys():
        refList.update({key: []})
        _physicalSegs.update({key: []})
    for feature in SegLayer.getFeatures():
        if feature['Physical']:
            lineGeo = feature.geometry().asPolyline()
            id1 = nodeRef[lineGeo[0]]
            id2 = nodeRef[lineGeo[-1]]
            physName = feature['Physical']
            ref = physicCode(physName, physicsRef)
            refList[ref].append(id1)
            refList[ref].append(id2)
            _physicalSegs[ref].append([id1, id2])

    if _physicalSegs:
        arrangedSegs = headAndTail(refList, _physicalSegs)
        keyList = sorted(arrangedSegs.keys())

        for key in keyList:
            nodeList = arrangedSegs[key]
            for nodes in nodeList:
                id1 = nodes[0]
                id2 = nodes[1]
                line = ("1 2 " + str(key) + " 0 " + str(id1) + " " + str(id2) +
                        "\n")
                physicalLines.append(line)

    return physicalLines


def makeDict(c_phySeq):
    newDict = dict()
    for i in range(0, len(c_phySeq)):
        newDict.update({c_phySeq[i]: i})
    return newDict


def getGridNames(NodeLayer, SegLayer, ZoneLayer):
    pointPhysics = list()
    for feature in NodeLayer.getFeatures():
        if feature['Physical'] != None:
            pointPhysics.append(feature['Physical'])
    pointPhysics = set(pointPhysics)

    linePhysics = list()
    for feature in SegLayer.getFeatures():
        if feature['Physical'] != None:
            linePhysics.append((feature['Physical'], feature['seq']))
    linePhysics = set(linePhysics)

    zonePhysics = list()
    for feature in ZoneLayer.getFeatures():
        if feature['Zone'] != None:
            zonePhysics.append(feature['Zone'])
    zonePhysics = set(zonePhysics)

    return pointPhysics, linePhysics, zonePhysics


def meshOutput(meshFile, NodeLayer, SegLayer, ZoneLayer, regionOrder):
    physicsRef = dict()
    nodeRef = lineFrame.pointRefDict()
    pointPhysics, linePhysics, zonePhysics = getGridNames(
        NodeLayer, SegLayer, ZoneLayer)
    linePhysics = list(linePhysics)
    linePhysics = sorted(linePhysics, key=itemgetter(1))
    counter = 1
    if pointPhysics:
        for physic in pointPhysics:
            physicsRef.update({counter: [physic, 0]})
            counter = counter + 1
    if linePhysics:
        for physic in linePhysics:
            physicsRef.update({counter: [physic[0], 1]})
            counter = counter + 1
    if zonePhysics:
        for zone in regionOrder:
            physicsRef.update({counter: [zone, 2]})
            counter += 1

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

    f.write("$Elements\n")
    f.write(str(len(physicalNodes) + len(physicalSegs) +
                ZoneLayer.featureCount()) + "\n")
    elementCount = 1
    # Output of Nodes
    for line in physicalNodes:
        f.write(str(elementCount) + " " + line)
        elementCount = elementCount + 1

    # Output of Boundaries
    for line in physicalSegs:
        f.write(str(elementCount) + " " + line)
        elementCount = elementCount + 1

    #  Output of mesh
    for feature in ZoneLayer.getFeatures():
        distri = feature['Zone']
        geo = feature.geometry().asPolygon()
        geo[0].pop(-1)
        ref = physicCode(distri, physicsRef)
        line = (str(len(geo[0])-1) + " 2 " + str(ref) + " 0 ")

        for point in geo[0]:
            fid = nodeRef[point]
            line = line + str(fid) + " "
        line = line[:-1] + "\n"

        f.write(str(elementCount) + " " + line)
        elementCount = elementCount + 1

    f.write("$EndElements")
    f.close()
    iface.messageBar().pushMessage(meshFile+' Mesh output done.')


def dictToList(physDict):
    seq = physDict.values()
    seq.sort()

    physList = list()
    for i in range(0, len(seq)):
        for key in physDict.keys():
            if physDict[key] == seq[i]:
                physList.append(key)
    return physList


def countPhysics(lineLayer):
    allphysics = list()
    for feature in lineLayer.getFeatures():
        if feature['Physical']:
            allphysics.append(feature['Physical'])

    allphysics = set(allphysics)
    allphysics = list(allphysics)
    allphysics.sort()

    NumberedPhysics = list()
    for feature in lineLayer.getFeatures():
        if feature['Physical'] and feature['seq']:
            NumberedPhysics.append((feature['Physical'], feature['seq']))
    NumberedPhysics = set(NumberedPhysics)
    try:
        NumberedPhysics = sorted(NumberedPhysics, key=itemgetter(1))
    except:
        pass
    _NumberedPhysics = list()
    if NumberedPhysics:
        for physName in NumberedPhysics:
            _NumberedPhysics.append(physName[0])

    for name in allphysics:
        if name not in _NumberedPhysics:
            _NumberedPhysics.append(name)

    return _NumberedPhysics


def mshPreview(filename, crs, outDir, dlg):
    meshfile = open(filename, 'r')
    meshName = filename.split('/')[-1]
    mesh = meshfile.readlines()
    meshfile.close()

    vertices = dict()
    physicalNames = dict()
    layerPath = dict()
    physicalWriter = dict()
    NodeFeature = dict()
    mode = 0
    endStatements = ["$EndPhysicalNames", "$EndNodes", "$EndElements"]

    fields = QgsFields()
    fields.append(QgsField("id", QVariant.Int))

    counter = 0
    for l in mesh:
        w = l.split()

        if not w:
            pass
        elif w[0] == "$PhysicalNames":
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
            path = os.path.join(outDir, name + ".shp")

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
            layerPath.update({3+tag: path})

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
            elif NodesNum > 2:
                geoString = "POLYGON (("
                ElementNodes.append(ElementNodes[0])
                for pid in ElementNodes:
                    x, y, z = vertices[int(pid)]
                    geoString = geoString + str(x) + " " + str(y) + ","
                geoString = geoString[:-1] + "))"
                feature.setGeometry(QgsGeometry().fromWkt(geoString))

            feature.setAttributes([int(fid)])
            writer.addFeature(feature)
        elif mode == 0:
            continue
        elif len(w) == 1:
            continue
        counter = counter + 1
        dlg.mshPreviewBar.setValue(int(float(counter)/len(mesh)*100))

    for writer in physicalWriter.values():
        del writer

    for key in NodeFeature.keys():
        feature = QgsFeature()
        geoString = NodeFeature[key][0]
        Z = NodeFeature[key][1]
        phys = NodeFeature[key][2]
        feature.setGeometry(QgsGeometry().fromWkt(geoString))
        feature.setAttributes([key, Z, phys])

    dlg.mshPreviewBar.setValue(100)
    loadMeshLayers(layerPath, meshName)


def randColor():
    color = (randint(0, 255), randint(0, 255), randint(0, 255))
    return '#' + ''.join(map(chr, color)).encode('hex')
