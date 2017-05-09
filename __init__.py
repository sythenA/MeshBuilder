# -*- coding: utf-8 -*-
"""
/***************************************************************************
 meshBuilder
                                 A QGIS plugin
 Build mesh for SRH2D
                             -------------------
        begin                : 2017-05-02
        copyright            : (C) 2017 by ManySplendid.co
        email                : yengtinglin@manysplendid.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load meshBuilder class from file meshBuilder.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .meshBuilder import meshBuilder
    return meshBuilder(iface)
