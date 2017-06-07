# -*- coding: big5 -*-

import os
import os.path
import re
from PyQt4.QtCore import QSettings, qVersion, QTranslator, QCoreApplication
from PyQt4.QtGui import QTableWidgetItem, QComboBox, QLineEdit, QPushButton
from PyQt4.QtGui import QFileDialog
from shepredDialog import shepredDialog
from commonDialog import onCritical, onWarning, onComment
from commonDialog import fileBrowser, folderBrowser


def read2dmMesh(meshLines):
    region = list()
    NScount = 0
    for line in meshLines:
        w = line.split()
        if w[0] in ['E3T', 'E4Q', 'E6T', 'E8Q', 'E9Q']:
            if not int(w[-1]) in region:
                region.append(int(w[-1]))
        elif w[0] == 'NS':
            if int(w[-1]) < 0:
                NScount = NScount + 1
    return region, NScount


def readMshMesh(filePath):
    start = False
    physicRef = dict()
    boundsRef = dict()
    f = open(filePath, 'r')
    line = f.readline()
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
                physicRef.update({int(w[1]): w[2].replace('"', '')})
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

    def fillMannTable(self):
        if self.dlg.rbtnManningConstant.isChecked():
            self.constantManning()
        elif self.dlg.rbtnManningMaterial.isChecked():
            self.mannMaterial()
        elif self.dlg.rbtnManningDistributed.isChecked():
            self.distriMann()

    def run(self):
        onComment(self.dlg.mannLabel, 1006)
        onComment(self.dlg.initLabel, 1000)
        meshFileCaption = u'請選擇輸入網格(.2dm格式)'
        self.dlg.pbtnFileSelector.clicked.connect(
            lambda: fileBrowser(self.dlg, meshFileCaption,
                                os.path.expanduser("~"),
                                self.dlg.lineEditMeshFileName,
                                presetType='.2dm'))
        meshFileCaption2 = u'請選擇輸入網格(.msh格式)'
        self.dlg.mshFileSelector.clicked.connect(
            lambda: fileBrowser(self.dlg, meshFileCaption2,
                                os.path.expanduser("~"),
                                self.dlg.lineMeshFilePath,
                                presetType='.msh'))

        saveFolderCaption = u'請選擇儲存SIF檔案的資料夾'
        self.dlg.saveFolderBtn.clicked.connect(
            lambda: folderBrowser(self.dlg,
                                  saveFolderCaption, os.path.expanduser("~"),
                                  lineEdit=self.dlg.saveFolderEdit))
        self.dlg.readMeshBtn.clicked.connect(self.readMesh)
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
        self.dlg.addIntvBtn.clicked.connect(self.setIntvTable)
        self.dlg.deleteIntvBtn.clicked.connect(self.deleteIntvTableColumn)

        result = self.dlg.exec_()
        if result:
            pass

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
                                presetType='.*'))

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
            f.write('INTERVAL\n')
        elif self.dlg.asigOutBtn.isChecked():
            table = self.dlg.OutIntvTable
            column = table.columnCount()
            line = ""
            for j in range(0, column):
                line = line + table.item(0, j).text() + ' '
            line = line[:-1] + '\n'
            f.write(line)
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
                text = QTableWidgetItem(str(meshRegion[i]))
                for i in range(0, len(meshRegion)):
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

    def export(self):
        fileName = self.dlg.lineEditCaseName.text() + '_SOF.DAT'
        saveFolder = self.dlg.saveFolderEdit.text()
        fullPath = os.path.join(saveFolder, fileName)

        f = open(fullPath, 'w')

        f.write('// Simulation Description (not used by SRH-2D):\n')
        f.write(self.dlg.lineEditDescription.text()+'\n')
        f.write('\n')
        f.write('// Module/Solver Selected (FLOW MORP MOB TEM TC)\n')
        f.write(self.chooseSolver()+'\n')
        f.write('\n')
        f.write('// Monitor-Point-Info: NPOINT\n')
        f.write(str(0)+'\n')
        f.write('\n')
        f.write('// Steady-or-Unsteady (STEADY/UNS)\n')
        f.write(self.chooseSteady()+'\n')
        f.write('\n')
        f.write('// Tstart Time_Step and Total_Simulation_Time: TSTART DT \
T_SIMU [FLAG]\n')
        TSTART, DT, T_SIMU = self.timeSetup()
        f.write(str(TSTART) + " " + str(DT) + " " + str(T_SIMU)+'\n')

        f = self.onTubulenceModel(f)

        f = self.onInitial(f)
        f.write('// Mesh FILE_NAME and FORMAT(SMS...)\n')
        f.write("                    " +
                self.dlg.lineEditMeshFileName.text()+'\n')
        f.write('\n')
        f.write('// Manning Roughness Input Method(1=constant 2=material-type\
 3=(x y) distributed)\n')
        mannInput = self.getManningVal()
        if mannInput is None:
            f.write(str(3)+'\n')
        elif type(mannInput) == float:
            f.write(str(1)+'\n')
        elif type(mannInput) == list:
            f.write(str(2)+'\n')
            f.write('\n')
            f.write('// Number of Material Types\n')
            f.write(str(len(mannInput))+'\n')
            f.write('\n')
            f.write('// For each Material Type: Manning-Coef\n')
            for i in range(0, len(mannInput)):
                f.write(str(mannInput[i])+'\n')
                f.write('\n')
        f = self.boundaryOutput(f)
        f = self.onOutputFormat(f)
        f.write('// Headers of Output Variables specified by the User: EMPTY li\
ne means default is used\n')
        f.write('\n')
        f = self.onIntvOuput(f)

        f.close()
        self.dlg.label_Complete.setText(u'完成')

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
        f.write('\n')
        return f

    def boundaryOutput(self, f):
        table = self.dlg.boundaryTable
        rows = table.rowCount()
        wallRoughness = list()
        for i in range(0, rows):
            f.write('// Boundary Type (INLET-Q EXIT-H etc)\n')
            if table.cellWidget(i, 1).currentText() == 'INLET-Q':
                f.write('INLET-Q\n')
                f.write('\n')
                f.write('// Boundary Values (Q W QS TEM H_rough etc)\n')
                line = str(float(table.item(i, 2).text())) + " "
                line = line + table.cellWidget(i, 4).currentText()
                if table.cellWidget(i, 5).currentIndex() != 0:
                    line = (line + " " + table.cellWidget(i, 5).currentText() +
                            '\n')
                else:
                    line = line + '\n'
                f.write(line)
            elif table.cellWidget(i, 1).currentText() == 'EXIT-H':
                f.write('EXIT-H\n')
                f.write('\n')
                f.write('// Boundary Values (Q W QS TEM H_rough etc)\n')
                line = str(float(table.item(i, 3).text())) + " "
                line = line + table.cellWidget(i, 4).currentText() + '\n'
                f.write(line)
            elif table.cellWidget(i, 1).currentText() == 'EXIT-Q':
                f.write('EXIT-Q\n')
                f.write('\n')
                f.write('// Boundary Values (Q W QS TEM H_rough etc)\n')
                line = str(float(table.item(i, 2).text())) + " "
                line = line + table.cellWidget(i, 4).currentText()
                if table.cellWidget(i, 5).currentIndex() != 0:
                    line = (line + " " + table.cellWidget(i, 5).currentText() +
                            '\n')
                else:
                    line = line + '\n'
                f.write(line)
            elif table.cellWidget(i, 1).currentText() == 'INLET-SC':
                f.write('INLET-SC\n')
                f.write('\n')
                f.write('// Boundary Values (Q W QS TEM H_rough etc)\n')
                line = str(float(table.item(i, 2).text())) + " "
                line = line + str(float(table.item(i, 3).text()))
                line = line + table.cellWidget(i, 4).currentText() + '\n'
                f.write(line)
            elif table.cellWidget(i, 1).currentText() == 'EXIT-EX':
                f.write('EXIT-EX\n')
            elif table.cellWidget(i, 1).currentText() == 'EXIT-ND':
                f.write('EXIT-ND\n')
                f.write('\n')
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
            f.write('\n')

        if wallRoughness:
            for i in range(0, len(wallRoughness)):
                f.write('// WALL-ROUGHNESS-HEIGHT-SPECIFICATION: Boundary-Patch\
-ID\n')
                f.write(str(wallRoughness[i][0]+1) + '\n')
                f.write('\n')
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
                    mannValue.append(float(self.dlg.mannTable.item(2, i).text())
                                     )
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

        group = [self.dlg.rbtnTurbPARA, self.dlg.rbtnTurbKE]
        for btn in group:
            if btn.isChecked():
                selected = btn.text()

        if selected == 'PARA':
            f.write('PARA\n')
            f.write('\n')
            f.write('// A_TURB for the PARA Model (0.05 to 1.0)\n')
            if isfloat(self.dlg.turbParaInput.text()):
                f.write(self.dlg.turbParaInput.text()+'\n')
            else:
                onCritical(106)
        elif selected == 'KE':
            f.write('KE\n')
        f.write('\n')

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
                for j in range(0, 5):
                    line = line + table.item(i, j).text() + " "
                line = line[:-1] + '\n'
                f.write(line)

        f.write('// Mesh-Unit (FOOT METER INCH MM MILE KM GSCALE)\n')
        f.write(self.onMeshUnit()+'\n')
        f.write('\n')

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
            unitWidget = QComboBox()
            unitWidget.addItems(['SI', 'EN'])
            self.dlg.boundaryTable.setCellWidget(i, 4, unitWidget)
            v_disWidget = QComboBox()
            v_disWidget.addItems(['None', 'C', 'V', 'Q'])
            self.dlg.boundaryTable.setCellWidget(i, 5, v_disWidget)

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
            boundsRef, physRef = readMshMesh(self.dlg.lineMeshFilePath.text())

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
