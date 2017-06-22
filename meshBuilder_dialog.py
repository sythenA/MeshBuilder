# -*- coding: utf-8 -*-
"""
/***************************************************************************
 meshBuilderDialog
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

import os

from PyQt4 import QtGui, uic
from qgis.utils import iface
import pickle

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'meshBuilder_dialog_base.ui'))


class meshBuilderDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(meshBuilderDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.__parameter__ = dict()

    def closeEvent(self, event):
        if self.__parameter__:
            path = os.path.join(os.path.dirname(__file__), '__parameter__')
            f = open(path, 'wb')
            pickle.dump(self.__parameter__, f)
            f.close()

        iface.messageBar().pushMessage('Closed')
        self.accept()

        return QtGui.QDialog.closeEvent(self, event)
