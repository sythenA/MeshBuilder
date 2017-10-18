# -*- coding: big5 -*-
"""
/***************************************************************************
 TECViewDialog
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

import os

import re
from PyQt4 import QtGui, uic
from PyQt4.QtGui import QIcon, QPixmap

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'TECViewer_dialog_base.ui'))


class TECViewDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(TECViewDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.readSettings()
        self.loadIcon()
        self.selectProjFolder.setToolTip(u'設定專案資料夾')
        self.addFileBtn.setToolTip(u'選擇加入讀取清單中的TEC檔案')

    def readSettings(self):
        self.settings = dict()
        try:
            f = open(os.path.join(os.path.dirname(__file__), '_settings_'), 'r')
            dat = f.readlines()
            for line in dat:
                self.settings.update(
                    {re.split('=', line)[0]: re.split('=', line)[1]})
        except:
            f = open(os.path.join(os.path.dirname(__file__), '_settings_'), 'w')

    def loadIcon(self):
        pixMap = QPixmap(os.path.join(os.path.dirname(__file__),
                                      'Georeference.svg'))
        geoIcon = QIcon(pixMap)
        self.geoRefBtn.setIcon(geoIcon)
        self.geoRefBtn.setIconSize(0.7*pixMap.rect().size())
        self.geoRefBtn.setToolTip(u'設定參考座標系')
