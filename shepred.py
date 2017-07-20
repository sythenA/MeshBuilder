# -*- coding: big5 -*-

import os
import os.path
import re
from qgis.core import QGis
from PyQt4.QtCore import QSettings, qVersion, QTranslator, QCoreApplication, Qt
from PyQt4.QtCore import QObject
from PyQt4.QtGui import QTableWidgetItem, QComboBox, QLineEdit, QPushButton
from PyQt4.QtGui import QFileDialog, QPixmap
from shepredDialog import shepredDialog
from commonDialog import onCritical, onWarning, onComment, onInfo
from commonDialog import fileBrowser, folderBrowser
from sedimentMod import sedimentModule
from shutil import copyfile
import subprocess
import pickle


def read2dmMesh(meshLines):
    region = list()
    NScount = 0
    for line in meshLines:
        w = line.split()
        try:
            if w[0] in ['E3T', 'E4Q', 'E6T', 'E8Q', 'E9Q']:
                if not int(w[-1]) in region:
                    region.append(int(w[-1]))
            elif w[0] == 'NS':
                if int(w[-1]) < 0:
                    NScount = NScount + 1
        except:
            pass
    region.sort()
    return region, NScount


def readMshMesh(filePath):
    start = False
    physicRef = dict()
    boundsRef = dict()
    f = open(filePath, 'r')
    line = f.readline()
    regionCounter = 1
    while line:
        w = line.split()
        if w[0] == '$PhysicalNames':
            f.readline()
            line = f.readline()
            w = line.split()
            start = True
        elif w[0] == '$EndPhysicalNames':
            break

        if start:
            if int(w[0]) == 1:
                boundsRef.update({int(w[1]): w[2].replace('"', '')})
            elif int(w[0]) > 1:
                physicRef.update({regionCounter: w[2].replace('"', '')})
                regionCounter = regionCounter + 1
        line = f.readline()
    f.close()
    return boundsRef, physicRef


def isint(string):
    try:
        int(string)
        return True
    except:
        return False


def isfloat(string):
    try:
        float(string)
        return True
    except:
        return False


class shepred:
    def __init__(self, iface):
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

        self.dlg = shepredDialog()

        try:
            path = os.path.join(os.path.dirname(__file__), '__parameter__')
            f = open(path, 'rb')
            param = pickle.load(f)
            f.close()
            projFolder = param['projFolder'].replace('/', '\\')
            self.dlg.projFolder = projFolder
        except:
            param = dict()
            param.update({'projFolder': ''})
            projFolder = ''

        dirToPic = os.path.join(os.path.dirname(__file__), 'eq_Pic',
                                'Pressure_Unit.png')
        pic = QPixmap(dirToPic)
        self.dlg.label_34.setPixmap(pic)
        self.dlg.label_35.setPixmap(pic)

        dirToPic = os.path.join(os.path.dirname(__file__), 'eq_Pic',
                                'FallSpeed2.png')
        pic = QPixmap(dirToPic)
        self.dlg.label_37.setPixmap(pic)

        dirToPic = os.path.join(os.path.dirname(__file__), 'eq_Pic',
                                'SIconcentration.png')
        pic = QPixmap(dirToPic)
        self.dlg.label_36.setPixmap(pic)

        self.dlg.solverTabWidget.setCurrentIndex(0)
        self.dlg.tabWidget.setCurrentIndex(0)

        self.dlg.rbtnSediInput.setEnabled(False)
        self.dlg.callSrhpreBtn.setEnabled(False)
        self.dlg.callSRH2DBtn.setEnabled(False)
        onComment(self.dlg.mannLabel, 1006)
        onComment(self.dlg.initLabel, 1000)
        meshFileCaption = u'請選擇輸入網格(.2dm格式)'
        self.dlg.pbtnFileSelector.clicked.connect(
            lambda: fileBrowser(self.dlg, meshFileCaption,
                                param['projFolder'],
                                self.dlg.lineEditMeshFileName,
                                presetType='.2dm'))
        meshFileCaption2 = u'請選擇輸入網格(.msh格式)'
        self.dlg.mshFileSelector.clicked.connect(
            lambda: fileBrowser(self.dlg, meshFileCaption2,
                                param['projFolder'],
                                self.dlg.lineMeshFilePath,
                                presetType='.msh'))

        self.dlg.saveFolderEdit.setText(projFolder)
        saveFolderCaption = u'請選擇儲存SIF檔案的資料夾'
        self.dlg.saveFolderBtn.pressed.connect(
            lambda: folderBrowser(self.dlg,
                                  saveFolderCaption, Dir=projFolder,
                                  lineEdit=self.dlg.saveFolderEdit))
        self.dlg.readMeshBtn.pressed.connect(self.readMesh)
        self.dlg.rbtnManningConstant.pressed.connect(self.constantManning)
        self.dlg.rbtnManningMaterial.pressed.connect(self.mannMaterial)
        self.dlg.rbtnManningDistributed.pressed.connect(self.distriMann)

        self.dlg.exportBtn.clicked.connect(self.export)
        self.dlg.inputFileBtn.clicked.connect(self.setWidgetFileBrowser)

        self.dlg.rbtnICDry.pressed.connect(self.initialDry)
        self.dlg.rbtnICRst.pressed.connect(self.initialRST)
        self.dlg.rbtnICZonal.pressed.connect(self.initZonal)
        self.dlg.rbtnICAuto.pressed.connect(self.initAuto)
        self.dlg.fixIntvBtn.pressed.connect(self.fixOutputIntv)
        self.dlg.asigOutBtn.pressed.connect(self.userOutputIntv)
        self.dlg.addIntvBtn.pressed.connect(self.setIntvTable)
        self.dlg.deleteIntvBtn.pressed.connect(self.deleteIntvTableColumn)
        self.dlg.callSrhpreBtn.pressed.connect(self.callSrhpre)
        self.dlg.callSRH2DBtn.pressed.connect(self.callSRH2D)
        self.dlg.rbtnSpecialNone.setCheckState(Qt.Checked)
        self.dlg.tabSpecialOps.setEnabled(False)
        self.dlg.tabSpecialOps.setTabEnabled(0, False)
        self.dlg.tabSpecialOps.setTabEnabled(1, False)
        self.dlg.tabSpecialOps.setTabEnabled(2, False)
        self.dlg.rbtnSolverFlow.toggled.connect(self.flowChoosed)

        self.dlg.solverTabWidget.setTabEnabled(1, False)
        self.dlg.rbtnSolverMobile.toggled.connect(self.mobileEnabled)
        self.dlg.label_40.setText(u'')

    def getObsLayer(self):
        self.dlg.obsPointsLayerCombo.clear()

        layerItems = list()
        layerItems.append(u'')
        layers = self.iface.legendInterface().layers()
        for layer in layers:
            if layer.geometryType() == QGis.Point:
                layerItems.append(layer.name())
        self.dlg.obsPointsLayerCombo.addItems(layerItems)

    def flowChoosed(self):
        self.dlg.solverTabWidget.setTabEnabled(1, False)
        self.dlg.rbtnSediInput.setEnabled(False)

    def mobileEnabled(self):
        self.dlg.solverTabWidget.setTabEnabled(1, True)
        Mod = sedimentModule(self.dlg)
        self.sediMod = Mod
        self.dlg.rbtnSediInput.setEnabled(True)

    def fillMannTable(self):
        if self.dlg.rbtnManningConstant.isChecked():
            self.constantManning()
        elif self.dlg.rbtnManningMaterial.isChecked():
            self.mannMaterial()
        elif self.dlg.rbtnManningDistributed.isChecked():
            self.distriMann()

    def callSrhpre(self):
        onInfo(1008)
        folderPath = self.dlg.saveFolderEdit.text()
        appFolder = os.path.dirname(__file__)
        srcPath = os.path.join(appFolder, 'srhpre.bat')
        dstPath = os.path.join(folderPath, 'srhpre.bat')
        os.chdir(folderPath)
        copyfile(srcPath, dstPath)
        subprocess.Popen([dstPath])

    def callSRH2D(self):
        folderPath = self.dlg.saveFolderEdit.text()
        appFolder = os.path.dirname(__file__)
        srcPath = os.path.join(appFolder, 'srh2d.bat')
        dstPath = os.path.join(folderPath, 'srh2d.bat')
        os.chdir(folderPath)
        copyfile(srcPath, dstPath)
        subprocess.Popen([dstPath])

    def addSource(self):
        self.dlg.rbtnSpecialNone.setCheckState(Qt.Unchecked)
        if self.dlg.rbtnSpecialMomentumless.checkState() == Qt.Checked:
            self.dlg.tabSpecialOps.setEnabled(True)
            self.dlg.tabSpecialOps.setTabEnabled(0, True)
        else:
            self.dlg.tabSpecialOps.setTabEnabled(0, False)

    def addInfil(self):
        self.dlg.rbtnSpecialNone.setCheckState(Qt.Unchecked)
        if self.dlg.rbtnSpecialInfiltration.checkState() == Qt.Checked:
            self.dlg.tabSpecialOps.setEnabled(True)
            self.dlg.tabSpecialOps.setTabEnabled(1, True)
        else:
            self.dlg.tabSpecialOps.setTabEnabled(1, False)

    def setNoSpecials(self):
        if self.dlg.rbtnSpecialNone.checkState == Qt.Checked:
            self.dlg.tabSpecialOps.setTabEnabled(0, False)
            self.dlg.tabSpecialOps.setTabEnabled(1, False)
            self.dlg.tabSpecialOps.setTabEnabled(2, False)

    def run(self):
        self.dlg.rbtnSpecialMomentumless.stateChanged.connect(self.addSource)
        self.dlg.rbtnSpecialInfiltration.stateChanged.connect(self.addInfil)
        self.dlg.rbtnSpecialNone.stateChanged.connect(self.setNoSpecials)

        self.getObsLayer()

        self.dlg.show()

    def initAuto(self):
        if self.dlg.rbtnSimUnsteady.isChecked():
            onWarning(302)
        onComment(self.dlg.initLabel, 1002)
        self.dlg.rstFileEdit.setEnabled(False)
        self.dlg.addRstFileBtn.setEnabled(False)
        self.dlg.InitCondTable.setEnabled(False)

    def initZonal(self):
        self.dlg.rstFileEdit.setEnabled(False)
        self.dlg.addRstFileBtn.setEnabled(False)
        self.dlg.InitCondTable.setEnabled(True)
        onComment(self.dlg.initLabel, 1003)

        table = self.dlg.InitCondTable
        table.setColumnCount(5)
        header = ['U', 'V', u'平均水位', u'紊流動能', u'紊流動能消散']
        table.setHorizontalHeaderLabels(header)

        if (self.dlg.lineEditMeshFileName.text() and
                self.dlg.lineMeshFilePath.text()):
            try:
                physName = self.physName
                table.setRowCount(len(physName))
                table.setVerticalHeaderLabels(physName)
            except(AttributeError):
                onCritical(114)
        elif (self.dlg.lineEditMeshFileName.text() and not
                self.dlg.lineMeshFilePath.text()):
            try:
                meshRegion = sorted(self.meshRegion)
                for i in range(0, len(meshRegion)):
                    meshRegion[i] = str(meshRegion[i])
                table.setRowCount(len(meshRegion))
                table.setVerticalHeaderLabels(meshRegion)
            except(AttributeError):
                onCritical(114)
        else:
            onCritical(114)

    def initialDry(self):
        onComment(self.dlg.initLabel, 1000)
        self.dlg.rstFileEdit.setEnabled(False)
        self.dlg.addRstFileBtn.setEnabled(False)
        self.dlg.InitCondTable.setEnabled(False)

    def initialRST(self):
        onComment(self.dlg.initLabel, 1001)
        self.dlg.rstFileEdit.setEnabled(True)
        self.dlg.addRstFileBtn.setEnabled(True)
        self.dlg.InitCondTable.setEnabled(False)

        caption = u'請選擇SRH2D中繼檔(_RST*.dat)'
        self.dlg.addRstFileBtn.clicked.connect(
            lambda: fileBrowser(self.dlg, caption, os.path.expanduser("~"),
                                lineEdit=self.dlg.rstFileEdit,
                                presetType='*.dat'))

    def setIntvTable(self):
        table = self.dlg.OutIntvTable
        count = table.columnCount()
        table.insertColumn(count)
        table.setItem(0, count,
                      QTableWidgetItem(str(self.dlg.outIntvEdit.text())))

    def deleteIntvTableColumn(self):
        table = self.dlg.OutIntvTable
        col = table.currentColumn()
        table.removeColumn(col)

    def onIntvOuput(self, f):
        f.write('// Intermediate Result Output Control: INTERVAL(hour) OR List \
of T1 T2 ...  EMPTY means the end\n')
        if self.dlg.fixIntvBtn.isChecked():
            if self.dlg.outIntvEdit.text():
                f.write(self.dlg.outIntvEdit.text() + '\n')
            else:
                f.write('1\n')
        elif self.dlg.asigOutBtn.isChecked():
            table = self.dlg.OutIntvTable
            column = table.columnCount()
            line = ""
            for j in range(0, column):
                line = line + table.item(0, j).text() + ' '
            line = line[:-1] + '\n'
            f.write(line)
            f.write('\n')
        return f

    def fixOutputIntv(self):
        self.dlg.outIntvEdit.setEnabled(False)
        self.dlg.addIntvBtn.setEnabled(False)
        self.dlg.deleteIntvBtn.setEnabled(False)
        self.dlg.OutIntvTable.setEnabled(False)

        onComment(self.dlg.initLabel, 1004)

    def userOutputIntv(self):
        self.dlg.outIntvEdit.setEnabled(True)
        self.dlg.addIntvBtn.setEnabled(True)
        self.dlg.deleteIntvBtn.setEnabled(True)
        self.dlg.OutIntvTable.setEnabled(True)
        self.dlg.OutIntvTable.setRowCount(1)

        onComment(self.dlg.initLabel, 1005)

    def constantManning(self):
        onComment(self.dlg.mannLabel, 1006)
        self.dlg.mannTable.clear()
        self.dlg.mannTable.setRowCount(3)
        self.dlg.mannTable.setColumnCount(1)

        self.dlg.mannTable.setItem(0, 0, QTableWidgetItem(str(1)))
        self.dlg.mannTable.setItem(1, 0, QTableWidgetItem('All Region'))

    def mannMaterial(self):
        onComment(self.dlg.mannLabel, 1007)
        self.dlg.mannTable.clear()
        if (self.dlg.lineEditMeshFileName.text() and
                self.dlg.lineMeshFilePath.text()):
            try:
                physName = self.physName
                self.dlg.mannTable.setRowCount(3)
                self.dlg.mannTable.setColumnCount(len(physName))
                item = QTableWidgetItem(str(len(physName)))
                self.dlg.mannTable.setItem(0, 0, item)
                for i in range(0, len(physName)):
                    self.dlg.mannTable.setItem(1, i,
                                               QTableWidgetItem(physName[i]))
            except(AttributeError):
                onCritical(114)
        elif (self.dlg.lineEditMeshFileName.text() and not
                self.dlg.lineMeshFilePath.text()):
            try:
                meshRegion = sorted(self.meshRegion)
                self.dlg.mannTable.setRowCount(3)
                self.dlg.mannTable.setColumnCount(len(meshRegion))
                item = QTableWidgetItem(str(len(meshRegion)))
                self.dlg.mannTable.setItem(0, 0, item)
                for i in range(0, len(meshRegion)):
                    text = QTableWidgetItem(str(meshRegion[i]))
                    self.dlg.mannTable.setItem(1, i, text)
            except(AttributeError):
                onCritical(114)
        else:
            onCritical(114)

    def distriMann(self):
        self.dlg.mannTable.clear()
        self.dlg.mannTable.setRowCount(1)
        self.dlg.mannTable.setColumnCount(2)

        distriMannEdit = QLineEdit()
        self.dlg.mannTable.setCellWidget(0, 0, distriMannEdit)
        button = QPushButton()
        button.setText('...')
        caption = u'請選擇點位型式之曼寧n值檔案'
        button.clicked.connect(lambda: fileBrowser(self.dlg, caption,
                                                   os.path.expanduser("~"),
                                                   lineEdit=distriMannEdit,
                                                   presetType=".*"))
        self.dlg.mannTable.setCellWidget(0, 1, button)

    def exportObsPoints(self, f):
        layerName = self.dlg.obsPointsLayerCombo.currentText()
        if layerName:
            obsPointsLayer = ''
            layers = self.iface.legendInterface().layers()
            for layer in layers:
                if layerName == layer.name():
                    obsPointsLayer = layer
            if obsPointsLayer:
                if obsPointsLayer.featureCount() > 99:
                    onCritical(128)

            if obsPointsLayer:
                f.write(str(obsPointsLayer.featureCount()) + '\n')
                f.write('// Monitor Point Coordinates: x1 y1 x2 y2 ...\n')
                line = ''
                for feature in obsPointsLayer.getFeatures():
                    x = feature.geometry().asPoint()[0]
                    y = feature.geometry().asPoint()[1]
                    line += (str(x) + ' ' + str(y) + ' ')
                line = line[:-1] + '\n'
                f.write(line)
            else:
                f.write('0\n')
        else:
            f.write('0\n')

        return f

    def export(self):
        fileName = self.dlg.lineEditCaseName.text() + '_SIF.DAT'
        saveFolder = self.dlg.saveFolderEdit.text()
        fullPath = os.path.join(saveFolder, fileName)
        useMobile = False

        f = open(fullPath, 'w')

        if self.dlg.rbtnSolverMobile.isChecked():
            sediMod = self.sediMod
            sediMod.sediExport()
            useMobile = True

        f.write('// Simulation Description (not used by SRH-2D):\n')
        f.write(self.dlg.lineEditDescription.text()+'\n')
        f.write('// Module/Solver Selected (FLOW MORP MOB TEM TC)\n')
        f.write(self.chooseSolver()+'\n')
        f.write('// Monitor-Point-Info: NPOINT\n')
        f = self.exportObsPoints(f)
        if not useMobile:
            f.write('// Steady-or-Unsteady (STEADY/UNS)\n')
            f.write(self.chooseSteady()+'\n')
        f.write('// Tstart Time_Step and Total_Simulation_Time: TSTART DT \
T_SIMU [FLAG]\n')
        TSTART, DT, T_SIMU = self.timeSetup()
        f.write(str(TSTART) + " " + str(DT) + " " + str(T_SIMU)+'\n')

        if self.dlg.rbtnSolverMobile.isChecked():
            f.write(sediMod.quasiString)

        f = self.onTubulenceModel(f)

        if useMobile:
            f.write(sediMod.sediGradText)
            f.write(sediMod.capacityText)
            f.write(sediMod.cohText)

        f = self.onInitial(f)
        f.write('// Mesh FILE_NAME and FORMAT(SMS...)\n')
        f.write(self.dlg.lineEditMeshFileName.text()+' SMS \n')
        #  Bed Properties (If use Mobile)
        if useMobile:
            f.write(sediMod.bedLayerText)

        f.write('// Manning Roughness Input Method(1=constant 2=material-type\
 3=(x y) distributed)\n')
        mannInput = self.getManningVal()
        if mannInput is None:
            f.write(str(3)+'\n')
        elif type(mannInput) == float:
            f.write(str(1)+'\n')
        elif type(mannInput) == list:
            f.write(str(2)+'\n')
            f.write('// Number of Material Types\n')
            f.write(str(len(mannInput))+'\n')
            f.write('// For each Material Type: Manning-Coef\n')
            for i in range(0, len(mannInput)):
                f.write(str(mannInput[i])+'\n')

        f.write('// Any-Special-Modeling-Options? (0/1=no/yes)\n')
        f.write(str(0) + '\n')

        if self.dlg.rbtnSolverMobile.isChecked():
            sediMod.bankExport()
            f.write(sediMod.bankText)

        f = self.boundaryOutput(f)
        f.write('// Number of In-Stream Flow Obstructions:\n')
        f.write(str(0) + '\n')
        f = self.onOutputFormat(f)
        f.write('// Headers of Output Variables specified by the User: EMPTY li\
ne means default is used\n')
        f.write('\n')
        f = self.onIntvOuput(f)

        f.close()
        self.dlg.label_Complete.setText(u'完成')
        onInfo(1009)
        self.dlg.callSrhpreBtn.setEnabled(True)
        self.dlg.callSRH2DBtn.setEnabled(True)

    def onOutputFormat(self, f):
        f.write('// Results-Output-Format-and-Unit(SRHC/TEC/SRHN/XMDF;SI/EN)\n')
        if self.dlg.rbtnOutputSMS.isChecked():
            line = "SRHN"
        elif self.dlg.rbtnOutputTecplot.isChecked():
            line = "TEC"

        if self.dlg.rbtnOutputUnitSI.isChecked():
            line = line + " " + "SI\n"
        elif self.dlg.rbtnOutputUnitEN.isChecked():
            line = line + " " + "EN\n"

        f.write(line)
        return f

    def boundaryOutput(self, f):
        def checkStage(text):
            if not text:
                onCritical(118)

        def checkFlowRate(text):
            if not text:
                onCritical(119)

        table = self.dlg.boundaryTable
        rows = table.rowCount()
        wallRoughness = list()
        for i in range(0, rows):
            f.write('// Boundary Type (INLET-Q EXIT-H etc)\n')
            if table.cellWidget(i, 1).currentText() == 'INLET-Q':
                f.write('INLET-Q\n')
                f.write('// Boundary Values (Q W QS TEM H_rough etc)\n')
                checkFlowRate(table.item(i, 2).text())
                line = str(table.item(i, 2).text()) + " "
                #  Sediment input(If Mobile is used)
                if self.dlg.rbtnSolverMobile.isChecked():
                    capacityCombo = self.dlg.sediBoundaryTable.cellWidget(i, 2)
                    if capacityCombo.currentIndex() == 0:
                        line += (capacityCombo.currentText() + ' ')
                    else:
                        line += (self.dlg.sediBoundaryTable.item(i, 3).text() +
                                 ' ')
                line = line + table.cellWidget(i, 4).currentText()

                if table.cellWidget(i, 5).currentIndex() != 0:
                    line = (line + " " + table.cellWidget(i, 5).currentText() +
                            '\n')
                else:
                    line = line + '\n'
                f.write(line)

            elif table.cellWidget(i, 1).currentText() == 'EXIT-H':
                f.write('EXIT-H\n')
                f.write('// Boundary Values (Q W QS TEM H_rough etc)\n')
                checkStage(table.item(i, 3).text())
                line = str(table.item(i, 3).text()) + " "
                line = line + table.cellWidget(i, 4).currentText() + '\n'
                f.write(line)
            elif table.cellWidget(i, 1).currentText() == 'EXIT-Q':
                f.write('EXIT-Q\n')
                f.write('// Boundary Values (Q W QS TEM H_rough etc)\n')
                checkFlowRate(table.item(i, 2).text())
                line = str(table.item(i, 2).text()) + " "
                line = line + table.cellWidget(i, 4).currentText()
                if table.cellWidget(i, 5).currentIndex() != 0:
                    line = (line + " " + table.cellWidget(i, 5).currentText() +
                            '\n')
                else:
                    line = line + '\n'
                f.write(line)
            elif table.cellWidget(i, 1).currentText() == 'INLET-SC':
                f.write('INLET-SC\n')
                f.write('// Boundary Values (Q W QS TEM H_rough etc)\n')
                checkFlowRate(table.item(i, 2).text())
                checkStage(table.item(i, 3).text())
                line = str(table.item(i, 2).text()) + " "
                line = line + str(table.item(i, 3).text())
                line = line + table.cellWidget(i, 4).currentText() + '\n'
                f.write(line)
            elif table.cellWidget(i, 1).currentText() == 'EXIT-EX':
                f.write('EXIT-EX\n')
            elif table.cellWidget(i, 1).currentText() == 'EXIT-ND':
                f.write('EXIT-ND\n')
                if table.item(i, 7) is None:
                    onCritical(112)
                else:
                    w = re.split(',\s|\s,|[\s,]', table.item(i, 7).text())
                    if len(w) < 3:
                        onCritical(113)
                    else:
                        f.write('// Q_METHOD(0_at_INLET_Q; >0_at_monitor; <0_lo\
cally, BED_SLOPE, WSE_MIN at the exit\n')
                        line = ""
                        for j in range(0, len(w)):
                            if w[j]:
                                line = line + w[j] + ' '
                            else:
                                pass
                        line = line[:-1] + '\n'
                        f.write(line)

            elif table.cellWidget(i, 1).currentText() == 'WALL':
                f.write('WALL\n')
                if table.item(i, 6) is not None:
                    if table.item(i, 6).text():
                        wallRoughness.append([i, table.item(i, 6).text()])
            elif table.cellWidget(i, 1).currentText() == 'SYMM':
                f.write('SYMM\n')
            elif table.cellWidget(i, 1).currentText() == 'MONITOR':
                f.write('MONITOR\n')

        if wallRoughness:
            for i in range(0, len(wallRoughness)):
                f.write('// WALL-ROUGHNESS-HEIGHT-SPECIFICATION: Boundary-Patch\
-ID\n')
                f.write(str(wallRoughness[i][0]+1) + '\n')
                f.write('// ROUGHNESS-HEIGHT-in-MillMeter\n')
                f.write(str(wallRoughness[i][1]) + '\n')
            f.write('\n')
        else:
            f.write('// Wall-Roughess-Height-Specification (empty-line=DONE)\n')
            f.write('\n')

        return f

    def getManningVal(self):
        if self.dlg.rbtnManningConstant.isChecked():
            if self.dlg.mannTable.item(2, 0) is not None:
                try:
                    mannValue = float(self.dlg.mannTable.item(2, 0).text())
                    return mannValue
                except:
                    onCritical(109)
            else:
                onCritical(110)
        elif self.dlg.rbtnManningMaterial.isChecked():
            count = self.dlg.mannTable.columnCount()
            self.dlg.label_9.setText(str(count))
            mannValue = list()
            for i in range(0, count):
                try:
                    mannValue.append(
                        float(self.dlg.mannTable.item(2, i).text()))
                except:
                    onCritical(110)
            return mannValue
        elif self.dlg.rbtnManningDistributed.isChecked():
            return None

    def chooseSolver(self):
        group = [self.dlg.rbtnSolverFlow, self.dlg.rbtnSolverMobile]
        for btn in group:
            if btn.isChecked():
                solverType = btn.text()

        solverType = solverType.upper()
        return solverType

    def chooseSteady(self):
        group = [self.dlg.rbtnSimSteady, self.dlg.rbtnSimUnsteady]
        for btn in group:
            if btn.isChecked():
                simType = btn.text().upper()
                return simType.upper()

    def timeSetup(self):
        tStart = self.dlg.lineEditTStart.text()
        tStep = self.dlg.lineEditTStep.text()
        totalTime = self.dlg.lineEditTTotal.text()

        if isint(tStart):
            tStart = float(tStart)
        else:
            onCritical(106)

        if isint(tStep):
            tStep = float(tStep)
        else:
            onCritical(106)

        if isint(totalTime):
            totalTime = float(totalTime)
        else:
            onCritical(106)

        return (tStart, tStep, totalTime)

    def outputUnit(self):
        group = [self.dlg.rbtnOutputUnitSI, self.dlg.rbtnOutputUnitEN]
        for btn in group:
            if btn.isChecked():
                return btn.text()

    def onTubulenceModel(self, f):
        f.write('// Turbulence-Model-Selection(PARA or KE)\n')

        group = [self.dlg.rbtnTurbPARA, self.dlg.rbtnTurbKE,
                 self.dlg.rbtnTurbRNG]
        for btn in group:
            if btn.isChecked():
                selected = btn.text()

        if selected == 'PARA':
            f.write('PARA\n')
            f.write('// A_TURB for the PARA Model (0.05 to 1.0)\n')
            if isfloat(self.dlg.turbParaInput.text()):
                f.write(self.dlg.turbParaInput.text()+'\n')
            else:
                onCritical(106)
        elif selected == 'KE':
            f.write('KE\n')
        elif selected == 'RNG':
            f.write('RNG\n')

        return f

    def onInitial(self, f):
        f.write('// Initial Condition Method (DRY RST AUTO ZONAL)\n')
        group = [self.dlg.rbtnICDry, self.dlg.rbtnICRst, self.dlg.rbtnICAuto,
                 self.dlg.rbtnICZonal]

        for btn in group:
            if btn.isChecked():
                f.write(btn.text()+'\n')

        if self.dlg.rbtnICZonal.isChecked():
            f.write('// Constant Setup for Initial Condition: n_zone [2DM_filen\
ame]\n')
            line = (str(len(self.meshRegion)) + " " +
                    self.dlg.lineEditMeshFileName.text() + '\n')
            f.write(line)
            table = self.dlg.InitCondTable
            row = table.rowCount()
            for i in range(0, row):
                f.write('// Constant-Value Initial Condition for Mesh Zone: U V\
WSE [TK] [ED] [T]\n')
                line = ""
                for j in range(0, 3):
                    line = line + table.item(i, j).text() + " "
                if (self.dlg.rbtnTurbKE.isChecked() or
                        self.dlg.rbtnTurbRNG.isChecked()):
                    if table.item(i, 3).text():
                        line = line + table.item(i, 3).text() + " "
                    else:
                        line = line + str(0) + " "
                    if table.item(i, 4).text():
                        line = line + table.item(i, 4).text() + " "
                    else:
                        line = line + str(0) + " "
                line = line[:-1] + '\n'
                f.write(line)
        elif self.dlg.rbtnICRst.isChecked():
            f.write(self.dlg.rstFileEdit.text() + '\n')

        f.write('// Mesh-Unit (FOOT METER INCH MM MILE KM GSCALE)\n')
        f.write(self.onMeshUnit()+'\n')

        return f

    def setBoundaryTable(self):
        labels = [u'邊界名稱', u'性質', u'流量(Q)', u'水位(H)', u'單位制',
                  u'速度分佈', u'邊界層厚度', u'額外條件']
        boundaryTypes = ['INLET-Q', 'EXIT-H', 'EXIT-Q', 'INLET-SC', 'EXIT-EX',
                         'EXIT-ND', 'WALL', 'SYMM', 'MONITOR']
        self.dlg.boundaryTable.clear()
        self.dlg.boundaryTable.setRowCount(self.NScount)
        self.dlg.boundaryTable.setColumnCount(8)
        self.dlg.boundaryTable.setHorizontalHeaderLabels(labels)
        for i in range(0, self.NScount):
            try:
                boundNames = self.boundNames
                item = QTableWidgetItem(boundNames[i])
            except(AttributeError):
                item = QTableWidgetItem(str(i+1))
            typeWidget = QComboBox()
            typeWidget.addItems(boundaryTypes)
            self.dlg.boundaryTable.setItem(i, 0, item)
            self.dlg.boundaryTable.setCellWidget(i, 1, typeWidget)
            typeWidget.currentIndexChanged.connect(
                self.setSediBoundaryEnableWidgets)
            self.dlg.boundaryTable.setItem(
                i, 2, QTableWidgetItem(u''))
            self.dlg.boundaryTable.setItem(
                i, 3, QTableWidgetItem(u''))
            unitWidget = QComboBox()
            unitWidget.addItems(['SI', 'EN'])
            self.dlg.boundaryTable.setCellWidget(i, 4, unitWidget)
            v_disWidget = QComboBox()
            v_disWidget.addItems(['None', 'C', 'V', 'Q'])
            self.dlg.boundaryTable.setCellWidget(i, 5, v_disWidget)
            self.dlg.boundaryTable.setItem(
                i, 6, QTableWidgetItem(u''))
            self.dlg.boundaryTable.setItem(
                i, 7, QTableWidgetItem(u''))

        sediLabels = [u'邊界名稱', u'性質', u'入流/出流計算', u'檔案']
        table2 = self.dlg.sediBoundaryTable
        table2.clear()
        table2.setRowCount(self.NScount)
        table2.setColumnCount(4)
        table2.setHorizontalHeaderLabels(sediLabels)
        for i in range(0, self.NScount):
            try:
                boundNames = self.boundNames
                item = QTableWidgetItem(boundNames[i])
            except(AttributeError):
                item = QTableWidgetItem(str(i+1))
            typeWidget = QComboBox()
            typeWidget.addItems(boundaryTypes)
            typeWidget.currentIndexChanged.connect(
                self.setSediBoundaryEnableWidgets)
            table2.setItem(i, 0, item)
            table2.setCellWidget(i, 1, typeWidget)
            InputWidget = QComboBox()
            InputWidget.addItem('CAPACITY')
            InputWidget.addItem('File')
            table2.setCellWidget(i, 2, InputWidget)
            InputWidget.currentIndexChanged.connect(
                lambda: self.setSedimentFlowFile(InputWidget.sender()))
            table2.setItem(i, 3, QTableWidgetItem(u''))
        table2.setColumnWidth(2, 100)
        table2.setColumnWidth(3, 300)

    def setSedimentFlowFile(self, obj):
        table = self.dlg.sediBoundaryTable
        c_Row = table.currentRow()

        if isinstance(obj, QComboBox):
            if obj.currentIndex() == 1:
                item = table.item(c_Row, 3)
                caption = 'Please choose a file of sediment inflow/outflow.'
                fileBrowser(self.dlg, caption, self.dlg.projFolder, item,
                            presetType='*.*')
            else:
                item = table.item(c_Row, 3)
                item.setText(u'')
        else:
            # The ComboBox in the last row of table does not return correct
            # sender(return QFrame rather than QComboBox), that with the signal
            # emitted, use current row of table to find correct combobox widget.
            obj = table.cellWidget(c_Row, 2)
            if obj.currentIndex() == 1:
                item = table.item(c_Row, 3)
                caption = 'Please choose a file of sediment inflow/outflow.'
                fileBrowser(self.dlg, caption, self.dlg.projFolder, item,
                            presetType='*.*')
            else:
                item = table.item(c_Row, 3)
                item.setText(u'')

    def setSediBoundaryEnableWidgets(self):
        boundaryTable = self.dlg.boundaryTable
        table = self.dlg.sediBoundaryTable
        for i in range(0, boundaryTable.rowCount()):
            widget = boundaryTable.cellWidget(i, 1)
            idx = widget.currentIndex()
            sediWidget = table.cellWidget(i, 1)
            sediWidget.setCurrentIndex(idx)
            sediWidget.setEnabled(False)

        sediAllowed = [0, 2, 3]
        for i in range(0, table.rowCount()):
            comboWig = table.cellWidget(i, 1)
            sediWig = table.cellWidget(i, 2)
            if comboWig.currentIndex() not in sediAllowed:
                sediWig.setEnabled(False)
            else:
                sediWig.setEnabled(True)

    def setWidgetFileBrowser(self):
        table = self.dlg.boundaryTable
        row = table.currentRow()
        column = table.currentColumn()
        caption = ""
        if column == 2:
            caption = u'請選擇流量的時間序列檔案'
        elif column == 3:
            caption = u'請選擇水位的時間序列(或率定曲線)檔案'
        else:
            pass

        if column == 2 or column == 3:
            fileName = QFileDialog.getOpenFileName(self.dlg, caption,
                                                   os.path.expanduser("~"))
            table.setItem(row, column, QTableWidgetItem(fileName))
        else:
            pass

    def onMeshUnit(self):
        group = [self.dlg.rbtnMUnitFOOT, self.dlg.rbtnMUnitGScale,
                 self.dlg.rbtnMUnitKM, self.dlg.rbtnMUnitMETER,
                 self.dlg.rbtnMUnitMile, self.dlg.rbtnMUnitinch,
                 self.dlg.rbtnMUnitmm]
        for btn in group:
            if btn.isChecked():
                return btn.text().upper()

    def readMesh(self):
        path2dm = self.dlg.lineEditMeshFileName.text()
        if not path2dm:
            onCritical(107)
        else:
            f = open(path2dm, 'r')
            meshLines = f.readlines()
            meshRegion, NScount = read2dmMesh(meshLines)
            self.NScount = NScount
            self.meshRegion = meshRegion

            self.fillMannTable()
            self.setBoundaryTable()
            if not self.dlg.lineMeshFilePath.text():
                onWarning(301)
            else:
                mshFilePath = self.dlg.lineMeshFilePath.text()
                boundsRef, physRef = readMshMesh(mshFilePath)

                boundNames = list()
                physNames = list()

                keylist = boundsRef.keys()
                keylist.sort()
                for key in keylist:
                    boundNames.append(boundsRef[key])

                meshRegion.sort()
                for dist in meshRegion:
                    physNames.append(physRef[dist])

                self.boundNames = boundNames
                self.physName = physNames
                self.physRef = physRef

                self.fillMannTable()
                self.setBoundaryTable()
