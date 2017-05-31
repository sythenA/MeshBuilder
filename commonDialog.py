from PyQt4.QtGui import QFileDialog, QMessageBox
import os
import os.path


def folderBrowser(parent, caption="", Dir=os.getcwd(),
                  lineEdit=""):
    folderName = QFileDialog.getExistingDirectory(parent, caption)
    if lineEdit:
        if folderName:
            lineEdit.setText(folderName)


def fileBrowser(parent, Caption, presetFolder, lineEdit="",
                presetType=".shp"):
    if not presetFolder:
        presetFolder = os.path.expanduser("~")

    fileName = QFileDialog.getOpenFileName(parent, Caption,
                                           presetFolder, "*" + presetType)
    if lineEdit:
        if fileName:
            lineEdit.setText(fileName)


def saveFileBrowser(parent, Caption, presetFolder, lineEdit="",
                    presetType=".shp"):
    if not presetFolder:
        presetFolder = os.path.expanduser("~")

    fileName = QFileDialog.getSaveFileName(parent, Caption,
                                           presetFolder, "*" + presetType)
    if fileName and lineEdit:
        lineEdit.setText(fileName)


def criticalBox(title, message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText(message)
    msg.setWindowTitle(title)
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec_()


def warningBox(title, message, lineEdit, lineEditText):

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
