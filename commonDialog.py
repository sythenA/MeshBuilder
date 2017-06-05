from PyQt4.QtGui import QFileDialog, QMessageBox
import os
import os.path

criticalMessages = dict()
warningMessages = dict()


def isint(string):
    try:
        int(string)
        return True
    except:
        return False


def textParse(text):
    for line in text:
        if not line:
            pass
        elif isint(line):
            num = int(line)
        elif 'title:' in line:
            title = line.replace('title:', '').decode('big5')
        elif 'detail:' in line:
            detail = line.replace('detail:', '').replace('/n',
                                                         '\n').decode('big5')
            if num < 300:
                criticalMessages.update({num: {'title': title,
                                               'detail': detail}})
            elif num >= 300:
                warningMessages.update({num: {'title': title,
                                              'detail': detail}})


cDir = os.path.dirname(__file__)
f1 = open(os.path.join(cDir, 'popMessages.txt'), 'r')
criticalText = f1.readlines()
textParse(criticalText)


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
    if lineEdit and lineEditText:
        if val == QMessageBox.Yes:
            lineEdit.setText(lineEditText)
        elif val == QMessageBox.No:
            lineEdit.clear()


def onCritical(num):
    title = criticalMessages[num]['title']
    detail = criticalMessages[num]['detail']

    criticalBox(title, detail)


def onWarning(num, lineEdit="", lineEditText=""):
    title = warningMessages[num]['title']
    detail = warningMessages[num]['detail']

    warningBox(title, detail, lineEdit, lineEditText)
