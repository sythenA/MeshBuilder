
from qgis.core import QGis, QgsGeometry
from qgis.utils import iface


def lineInverse(lineString):
    newString = list()
    length = len(lineString)
    for i in range(0, len(lineString)):
        newString.append(lineString[length-1-i])

    return newString


def flip():
    layer = iface.activeLayer()

    layer.startEditing()
    if layer.geometryType() == QGis.Line:
        features = layer.selectedFeatures()
        for feature in features:
            fid = feature.id()
            if feature.geometry().asPolyline():
                newGeometry = lineInverse(feature.geometry().asPolyline())
                layer.changeGeometry(
                    fid, QgsGeometry().fromPolyline(newGeometry))
            elif feature.geometry().asMultiPolyline():
                newGeo = list()
                for line in feature.geometry().asMultiPolyline():
                    newGeo.append(lineInverse(line))
                layer.changeGeoemtry(
                    fid, QgsGeometry().fromMultiPolyline(newGeo))

    layer.commitChanges()
