
from qgis.utils import iface
from qgis.core import QgsVectorFileWriter, QGis, QgsField, QgsFeature
from qgis.core import QgsVectorLayer, QgsGeometry, QgsPoint
from PyQt4.QtCore import QVariant, QFileInfo, QPyNullVariant
import collections
from math import sqrt


class TransformedDict(collections.MutableMapping):
    """A dictionary that applies an arbitrary key-altering
       function before accessing the keys"""
    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key):
        return self.store[self.__keytransform__(key)]

    def __setitem__(self, key, value):
        self.store[self.__keytransform__(key)] = value

    def __delitem__(self, key):
        del self.store[self.__keytransform__(key)]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __keytransform__(self, key):
        return key


class pointRefDict(TransformedDict):
    def __keytransform__(self, key):
        for rkey in self.keys():
            if sqrt((key[0]-rkey[0])**2 + (key[1]-rkey[1])**2) < 1.0e-3:
                return rkey
        return key


class lineRefDict(TransformedDict):
    def __keytransform__(self, key):
        if key not in self.keys():
            rkey = list()
            for i in range(0, len(key)):
                rkey.append(key[len(key)-1-i])
            return tuple(rkey)
        else:
            return key


class pointFrame:
    def __init__(self, projFolder, **kwargs):
        if 'orgPointsLayer' in kwargs.keys():
            self.pointLayer = kwargs['orgPointsLayer']
        self.projFolder = projFolder
        if 'CRS' in kwargs.keys():
            self.crs = kwargs['CRS']
        else:
            self.crs = ""

    def checkRepetitive(self, feature, featureList):
        rep = False  # repetitive checker
        for _feature in featureList:
            p1 = feature.geometry().asPoint()
            p2 = _feature.geometry().asPoint()
            dist = sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
            if dist < 1.0e-4:
                rep = True
        if not rep:
            featureList.append(feature)
        return featureList

    def copyPoint(self):
        pointLayer = self.pointLayer
        savePath = self.projFolder + '\\' + 'MainPoint_frame.shp'
        self.filePath = savePath
        fields = pointLayer.pendingFields()
        fields.append(QgsField('breakPoint', QVariant.Int))
        fields.append(QgsField('geoName', QVariant.String))

        if self.crs:
            CRS = self.crs
        else:
            CRS = None

        pointFrameWriter = QgsVectorFileWriter(savePath, 'utf-8', fields,
                                               QGis.WKBPoint, CRS,
                                               'ESRI shapefile')
        #  If repetitive, do not copy to the new layer.
        featureList = list()
        for feature in pointLayer.getFeatures():
            featureList = self.checkRepetitive(feature, featureList)

        geoNum = 0
        for feature in featureList:
            newFeature = QgsFeature()
            newFeature.setGeometry(QgsGeometry.fromPoint(
                                   feature.geometry().asPoint()))
            newFeature.setAttributes([feature['id'], feature['Name'],
                                      feature['mesh_size'], feature['Loop'],
                                      feature.geometry().asPoint().x(),
                                      feature.geometry().asPoint().y(),
                                      feature['Physical'], None,
                                      'IP+' + str(geoNum)])
            pointFrameWriter.addFeature(newFeature)
            geoNum = geoNum + 1

        del pointFrameWriter

    def showLayer(self):
        iface.addVectorLayer(self.filePath, QFileInfo(self.filePath).baseName(),
                             'ogr')

    def openLayer(self):
        projFolder = self.projFolder
        path = projFolder + '\\' + 'MainPoint_frame.shp'
        layer = QgsVectorLayer(path, QFileInfo(path).baseName(), 'ogr')
        self.frameLayer = layer


class lineFrame:
    def __init__(self, projFolder, **kwargs):
        #  lineLayer: the line data layer from original simmulation area
        #  (polygon).
        if 'orgLinesLayer' in kwargs.keys():
            self.lineLayer = kwargs['orgLinesLayer']
        self.projFolder = projFolder

        pointFramePath = projFolder + "\\" + 'MainPoint_frame.shp'
        pointFrame = QgsVectorLayer(pointFramePath,
                                    QFileInfo(pointFramePath).baseName(), 'ogr')
        self.pointDict = pointRef(pointFrame)

    def readPoint(self, pointFrame):
        self.pointDict = pointRef(pointFrame.frameLayer)

    def showLayer(self):
        iface.addVectorLayer(self.filePath,
                             QFileInfo(self.filePath).baseName(), 'ogr')

    def lineInverse(self, lineGeo):
        InverseGeo = list()
        for i in range(0, len(lineGeo)):
            InverseGeo.append(lineGeo[len(lineGeo)-1-i])
        return InverseGeo

    def checkRepetitive(self, feature, featureList):
        featureGeo = feature.geometry().asPolyline()
        a = [self.pointDict[featureGeo[0]], self.pointDict[featureGeo[1]]]
        rep = False
        for _feature in featureList:
            _featureGeo = _feature.geometry().asPolyline()
            b = [self.pointDict[_featureGeo[0]], self.pointDict[_featureGeo[1]]]

            verse = (a == b)
            inverse = (a == self.lineInverse(b))
            if verse or inverse:
                rep = True
        if not rep:
            featureList.append(feature)
        return featureList

    def copyLines(self):
        lineLayer = self.lineLayer
        pointDict = self.pointDict
        savePath = self.projFolder + '\\' + 'MainLines_frame.shp'
        self.filePath = savePath
        fields = lineLayer.pendingFields()
        fields.append(QgsField('ForceBound', QVariant.Int))
        fields.append(QgsField('geoName', QVariant.String))
        fields.append(QgsField('Transfinite', QVariant.Int))
        fields.append(QgsField('Cells', QVariant.Int))

        pointFrameWriter = QgsVectorFileWriter(savePath, 'utf-8', fields,
                                               QGis.WKBLineString, None,
                                               'ESRI shapefile')
        #  If repetitive, do not copy to the new layer.
        featureList = list()
        for feature in lineLayer.getFeatures():
            featureList = self.checkRepetitive(feature, featureList)

        geoNum = 0
        for feature in featureList:
            startCoor = feature.geometry().asPolyline()[0]
            endCoor = feature.geometry().asPolyline()[-1]

            startPoint = pointDict[startCoor]['geoName']
            endPoint = pointDict[endCoor]['geoName']

            if startPoint != endPoint:
                startPoint = int(startPoint.replace('IP+', ''))
                endPoint = int(endPoint.replace('IP+', ''))
                newFeature = QgsFeature()
                newFeature.setGeometry(QgsGeometry.fromPolyline(
                                    feature.geometry().asPolyline()))
                newFeature.setAttributes([feature['id'], feature['Name'],
                                          feature['Loop'], feature['Line_id'],
                                          startPoint, endPoint,
                                          feature['ForceBound'],
                                          feature['Physical'],
                                          str(geoNum), 0, 0])
                pointFrameWriter.addFeature(newFeature)
                geoNum = geoNum + 1

        del pointFrameWriter

    def openLayer(self):
        projFolder = self.projFolder
        path = projFolder + '\\' + 'MainLines_frame.shp'
        layer = QgsVectorLayer(path, QFileInfo(path).baseName(), 'ogr')
        self.frameLayer = layer


def pointRef(pointFrame):
    frameRef = pointRefDict()
    for feature in pointFrame.getFeatures():
        attr = dict()
        attr.update({'Name': feature['Name']})
        attr.update({'Physical': feature['Physical']})
        attr.update({'geoName': feature['geoName']})
        attr.update({'breakPoint': feature['breakPoint']})
        key = feature.geometry().asPoint()
        frameRef.update({key: attr})

    return frameRef


def lineRef(lineFrame, pointDict):
    frameRef = lineRefDict()
    for feature in lineFrame.getFeatures():
        geo = feature.geometry().asPolyline()
        attr = dict()
        attr.update({'Name': feature['Name']})
        attr.update({'ForceBound': feature['ForceBound']})
        attr.update({'Start_p': 'IP+' + str(feature['Start_p'])})
        attr.update({'End_p': 'IP+' + str(feature['End_p'])})
        attr.update({'Physical': feature['Physical']})
        attr.update({'geoName': feature['geoName']})
        attr.update({'fid': feature.id()})
        key = list()
        for point in geo:
            key.append(pointDict[point]['geoName'])
        key = tuple(key)
        frameRef.update({key: attr})

    return frameRef


def polygonBoundary(feature):
    polygonGeo = feature.geometry().asPolygon()
    loop = polygonGeo[0]
    lineString = list()
    for point in loop:
        lineString.append(point)

    lineGeo = QgsGeometry.fromPolyline(lineString)

    return lineGeo


def innerBoundaries(feature):
    polygonGeo = feature.geometry().asPolygon()
    lineGeos = list()
    if len(polygonGeo) > 1:
        for i in range(1, len(polygonGeo)):
            loopString = list()
            for point in polygonGeo[i]:
                loopString.append(point)
            lineGeos.append(QgsGeometry.fromPolyline(loopString))
    return lineGeos


def featureLoop(lineList):
    Loop = [str(lineList[0][2])]
    firstLine = lineList[0]
    Start0 = firstLine[0]
    End0 = firstLine[1]
    for i in range(1, len(lineList)):
        found = False
        for j in range(1, len(lineList)):
            Start1 = lineList[j][0]
            End1 = lineList[j][1]
            if Start1 == End0 and End1 != Start0:
                Loop.append(str(lineList[j][2]))
                found = True
                Start0 = Start1
                End0 = End1
                break
        if not found:
            for j in range(1, len(lineList)):
                Start1 = lineList[j][0]
                End1 = lineList[j][1]
                if End0 == End1 and Start0 != Start1:
                    Loop.append(str('-' + lineList[j][2]))
                    found = True
                    Start0 = End1
                    End0 = Start1
                    break
    return Loop


def combineAble(geo, anotherGeo, pointDict):
    conPoint = geo.intersection(anotherGeo).asPoint()
    if conPoint == QgsPoint(0, 0):
        return True
    val = pointDict[conPoint]['breakPoint']
    if type(val) == QPyNullVariant or val is None:
        return True
    else:
        if int(val) == 0:
            return True
        elif int(val) == 1:
            return False
        else:
            return True


def ifForce(feature):
    if (type(feature['ForceBound']) == QPyNullVariant or
            feature['ForceBound'] is None):
        return 0
    else:
        if int(feature['ForceBound']) == 0:
            return 0
        else:
            return 1


def geoInverse(geometry):
    pointList = list()
    line = geometry.asPolyline()
    for i in range(0, len(line)):
        pointList.append(line[len(line)-1-i])
    return QgsGeometry.fromPolyline(pointList)


def combine(feature, featureList, lineFrameLayer, pointDict, removeList):
    lineFrameLayer.startEditing()
    newGeometry = feature.geometry()
    for anotherFeature in featureList:
        a = ifForce(feature) == 0
        b = ifForce(anotherFeature) == 0
        anotherGeometry = anotherFeature.geometry()
        if newGeometry.touches(anotherGeometry):
            if a and b:
                if combineAble(newGeometry, anotherGeometry, pointDict):
                    newGeometry = newGeometry.combine(anotherGeometry)
                    lineFrameLayer.changeGeometry(feature.id(), newGeometry)
                    removeList.append(anotherFeature.id())
                elif (newGeometry.intersection(anotherGeometry).asPoint ==
                      QgsPoint(0, 0)):
                    line = newGeometry.asPolyline()
                    line.append(line[0])
                    newGeometry = QgsGeometry().fromPolyline(line)
        lineFrameLayer.changeGeometry(feature.id(), newGeometry)
    lineFrameLayer.commitChanges()
    return removeList


def lineCombine(lineFrameObj):
    """
    def changeOrient(line, pointDict):
        counter = 0
        for point in line:
            val = pointDict[point]['breakPoint']
            if not type(val) == QPyNullVariant and val is not None:
                if int(val) == 1:
                    break
            counter = counter + 1
        line.pop(-1)
        N = len(line)
        line = line[counter:N] + line[0:counter] + [line[counter]]
        return line"""

    lineFrameLayer = lineFrameObj.frameLayer
    pointDict = lineFrameObj.pointDict

    featureList = list()
    for feature in lineFrameLayer.getFeatures():
        featureList.append(feature)

    removeList = list()
    for feature in lineFrameLayer.getFeatures():
        if feature.id() not in removeList:
            removeList = combine(feature, featureList, lineFrameLayer,
                                 pointDict, removeList)
    lineFrameLayer.startEditing()
    lineFrameLayer.dataProvider().deleteFeatures(removeList)
    counter = 0
    for feature in lineFrameLayer.getFeatures():
        feature['geoName'] = str(counter)
        counter = counter + 1
        lineFrameLayer.updateFeature(feature)
    lineFrameLayer.commitChanges()

    lineFrameObj.lineFrameLayer = lineFrameLayer

    return lineFrameObj


def lineToLoop(lineFrameObj, polygonLayer):
    lineFrameLayer = lineFrameObj.frameLayer
    pointDict = lineFrameObj.pointDict
    lineDict = lineRef(lineFrameObj.frameLayer, pointDict)

    LoopDict = dict()
    counter = 1
    for feature in polygonLayer.getFeatures():
        boundary = polygonBoundary(feature)

        lineList = list()
        for lineFeat in lineFrameLayer.getFeatures():
            a = lineFeat.geometry().within(boundary)
            b = boundary.overlaps(lineFeat.geometry())
            lineIntersect = lineFeat.geometry().intersection(boundary)
            if a or b:
                key = list()
                for point in lineFeat.geometry().asPolyline():
                    key.append(pointDict[point]['geoName'])
                key = tuple(key)

                lineName = lineDict[key]['geoName']
                lineList.append((key[0], key[-1], lineName))

        LoopName = 'ILL+' + str(counter-1)
        counter = counter + 1
        print lineList
        LoopDict.update({feature['geoName']:
                         [{LoopName: featureLoop(lineList)}]})

        innerBound = innerBoundaries(feature)
        if innerBound:
            for boundLine in innerBound:
                lineList = list()
                for lineFeat in lineFrameLayer.getFeatures():
                    lineIntersect = lineFeat.geometry().intersection(boundLine)
                    if lineIntersect.equals(lineFeat.geometry()):
                        key = list()
                        for point in lineFeat.geometry().asPolyline():
                            key.append(pointDict[point]['geoName'])
                        key = tuple(key)

                        lineName = lineDict[key]['geoName']
                        lineList.append((key[0], key[-1], lineName))
                LoopName = 'ILL+' + str(counter-1)
                counter = counter + 1
                LoopDict[feature['geoName']].append({LoopName:
                                                     featureLoop(lineList)})

    return LoopDict
