# -*- coding: big5 -*-

import os
import os.path
from PyQt4.QtCore import QSettings, qVersion, QTranslator, QCoreApplication
from shepredDialog import shepredDialog
from commonDialog import onCritical, onWarning
from commonDialog import fileBrowser, folderBrowser, saveFileBrowser


def isint(string):
    try:
        int(string)
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

    def run(self):
        meshFileCaption = u'請選擇輸入網格(.2dm格式)'
        self.dlg.pbtnFileSelector.clicked.connect(lambda: fileBrowser(self.dlg,
            meshFileCaption, os.path.expanduser("~"),
            self.dlg.lineEditMeshFileName, presetType='.2dm'))

        saveFolderCaption = u'請選擇儲存SIF檔案的資料夾'
        self.dlg.saveFolderBtn.clicked.connect(lambda: folderBrowser(self.dlg,
            saveFolderCaption, os.path.expanduser("~"),
            lineEdit=self.dlg.saveFolderEdit))

        result = self.dlg.exec_()
        if result:
            pass

    def export(self):
        fileName = self.dlg.lineEditCaseName.text() + '_SIF.DAT'
        saveFolder = self.dlg.saveFolderEdit.text()
        fullPath = os.path.join(saveFolder, fileName)

        f = open(fullPath, 'w')

        f.write('// Simulation Description (not used by SRH-2D):\n')
        f.write(self.dlg.lineEditDescription.text()+'\n')
        f.wrtie('\n')
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
        f.write('// Turbulence-Model-Selection(PARA or KE)\n')
        f.write(self.onTubulentModel()+'\n')
        f.write('\n')



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
        totalTime = self.dlg.lineEditTTotal()

        if isint(tStart):
            tStart = int(tStart)
        else:
            onCritical(105)

        if isint(tStep):
            tStep = int(tStep)
        else:
            onCritical(105)

        if isint(totalTime):
            totalTime = int(totalTime)
        else:
            onCritical(105)

        return (tStart, tStep, totalTime)

    def onOutputFormat(self):
        group = [self.dlg.rbtnOutputSMS, self.dlg.rbtnOutputTecplot]
        for btn in group:
            if btn.isChecked():
                Oformat = btn.text()

        if Oformat == 'Tecplot':
            Oformat = 'TEC'
        elif Oformat == 'SMS':
            Oformat = 'SMS'
        else:
            onCritical(106)

        return Oformat

    def outputUnit(self):
        group = [self.dlg.rbtnOutputUnitSI, self.dlg.rbtnOutputUnitEN]
        for btn in group:
            if btn.isChecked():
                return btn.text()

    def onTubulentModel(self):
        group = [self.dlg.rbtnTurbPARA, self.dlg.rbtnTurbKE]
        for btn in group:
            if btn.isChecked():
                return btn.text()

    def onInitial(self):
        group = [self.dlg.rbtnICDry, self.dlg.rbtnICRst, self.dlg.rbtnICAuto,
                 self.dlg.rbtnICZonal]

        for btn in group:
            if btn.isChecked():
                return btn.text()

    def onMeshUnit(self):
        group = [self.dlg.rbtnMUnitFOOT, self.dlg.rbtnMUnitGScale,
                 self.dlg.rbtnMUnitKM, self.dlg.rbtnMUnitMETER,
                 self.dlg.rbtnMUnitMile, self.dlg.rbtnMUnitinch,
                 self.dlg.rbtnMUnitmm]
        for btn in group:
            if btn.isCkecked():
                return btn.text()

    def manningVal(self):
        group = [self.dlg.rbtnManningConstant, self.dlg.rbtnManningMaterial,
                 self.dlg.rbtnManningDistributed]
        for btn in group:
            if btn.isChecked():
                return btn.text()
