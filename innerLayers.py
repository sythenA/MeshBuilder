
import os
import os.path
import shutil
from lineFrame import pointRefDict, lineRefDict
from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsVectorFileWriter
from PyQt4.QtCore import QVariant, QFileInfo, QPyNullVariant


class innerLayersExport:
    def __init__(self, projFolder, baseLayer):
        self.folder = projFolder
        self.baseLayer = baseLayer
        self.innerLayers = list()
        self.surface_Num = baseLayer.featureCount()
        self.systemCRS = baseLayer.dataProvider().crs()

    def run(self):
        self.compareWithBase()
        self.seperateLayers(self.newlayers)
        self.inner_list = list()
        self.loopDict = dict()
        self.recombine = dict()
        self.surfaceSet = list()
        self.physicalSurfaces = dict()

        self.innerPointDict = pointRefDict()
        self.innerPointLayer = pointRefDict()
        self.innerLineDict = lineRefDict()
        self.innerLineLayer = lineRefDict()

    def copyLayers(self):
        folder = self.folder
        layerList = self.innerLayers

        #  A new attribute field: Surface
        newAttr = [QgsField('Surface', QVariant.Int)]
        crs = self.systemCRS
        newlayers = list()
        for layer in layerList:
            #  Retrive the absolute path to the shapfile
            baseName = layer.name()
            path = os.path.join(folder,
                                os.path.join('InnerLayers',
                                             str(baseName) + '.shp'))

            #  The vector layer data type (point, line, polygon)
            layerType = layer.wkbType()
            p_fields = layer.pendingFields()
            layerWriter = QgsVectorFileWriter(path, "utf-8", p_fields,
                                              layerType, crs, "ESRI Shapefile")
            for feature in layer.getFeatures():
                NewFeature = QgsFeature()  # Create an empty feature
                NewFeature.setGeometry(feature.geometry())
                #  Set feature geometry
                NewFeature.setAttributes(feature.attributes())
                #  Set attributes
                #  Update feature to the new layer
                layerWriter.addFeature(NewFeature)

            del layerWriter

            newlayer = QgsVectorLayer(path, QFileInfo(path).baseName(), 'ogr')
            newlayer.startEditing()
            #  Add new attribute field to layer
            newlayer.dataProvider().addAttributes(newAttr)
            newlayer.commitChanges()
            newlayers.append(newlayer)

        self.newlayers = newlayers
        self.addNewAttr()

    def addNewAttr(self):
        newLayers = self.newlayers
        for layer in newLayers:
            fields = layer.pendingFields()
            layer.startEditing()
            newAttr = list()
            if fields.fieldNameIndex('mesh_size') == -1:
                newAttr.append(QgsField('mesh_size', QVariant.Double))
            if fields.fieldNameIndex('Physical') == -1:
                newAttr.append(QgsField('Physical', QVariant.String))
                layer.dataProvider().addAttributes(newAttr)

            if layer.geometryType() == 1:
                if fields.fieldNameIndex('ForceBound') == -1:
                    newAttr.append(QgsField('ForceBound', QVariant.Int))
                if fields.fieldNameIndex('Transfinit') == -1:
                    newAttr.append(QgsField('Transfinit', QVariant.Int))
                if fields.fieldNameIndex('Cells') == -1:
                    newAttr.append(QgsField('Cells', QVariant.Int))
            elif layer.geometryType() == 2:
                if fields.fieldNameIndex('Empty') == -1:
                    newAttr.append(QgsField('Empty', QVariant.Int))
                if fields.fieldNameIndex('Recombine') == -1:
                    newAttr.append(QgsField('Recombine', QVariant.Int))
                if fields.fieldNameIndex('ForceBound') == -1:
                    newAttr.append(QgsField('ForceBound', QVariant.Int))

            layer.dataProvider().addAttributes(newAttr)
            layer.commitChanges()

        self.newlayers = newLayers

    def openLayers(self):
        layerList = list()
        projFolder = self.folder
        folder = os.path.join(projFolder, "InnerLayers")
        files = os.listdir(folder)
        openList = list()
        for File in files:
            if ".shp" in File:
                openList.append(File)
        for File in openList:
            path = os.path.join(folder, File)
            layer = QgsVectorLayer(path, QFileInfo(path).baseName(), 'ogr')
            layerList.append(layer)

        self.newlayers = layerList

    def compareWithBase(self):
        #  Identify the inner layer boundary, the features in the inner boundary
        #  layer #  are within the polygon boundaries in the main polygon layer,
        #  that the #  relation of inner layer features and polygons must be
        #  identified.
        #  (Which grid surface does this feature belong?)
        newlayers = self.newlayers
        BaseLayer = self.baseLayer
        for layer in newlayers:
            fields = layer.pendingFields()
            surf_idx = fields.fieldNameIndex('Surface')
            layer.startEditing()
            for feature in layer.getFeatures():
                found = 0  # Indicator: if a feature is find within a surface
                for polygon in BaseLayer.getFeatures():
                    if feature.geometry().within(polygon.geometry()):
                        #  If the feature is inside the polygon boundary
                        #  (in surface) #  , write the attribute of polygon
                        #  number info the feature.
                        feature[surf_idx] = polygon['geoName']
                        layer.updateFeature(feature)
                        found = 1
                feature[surf_idx] = None if found == 0 else 0
                layer.updateFeature(feature)
            layer.commitChanges()

        self.loop_num = BaseLayer.featureCount()

    def seperateLayers(self, newLayers):
        pointLayers = list()
        lineLayers = list()
        polygonLayers = list()

        for layer in newLayers:
            if layer.geometryType() == 0:
                pointLayers.append(layer)
            elif layer.geometryType() == 1:
                lineLayers.append(layer)
            else:
                polygonLayers.append(layer)

        self.pointLayers = pointLayers
        self.lineLayers = lineLayers
        self.polygonLayers = polygonLayers

    def writeInnerPoints(self, last_pid, p_Phx_list):
        pointDict = self.innerPointDict
        innerPoint_lines = list()
        for layer in self.pointLayers:
            fields = layer.pendingFields()
            surf_idx = fields.fieldNameIndex("Surface")
            p_Phx_idx = fields.fieldNameIndex("Physical")
            p_mesh_idx = fields.fieldNameIndex("mesh_size")
            for feature in layer.getFeatures():
                if type(feature[surf_idx]) != QPyNullVariant:
                    x = feature.geometry().asPoint()[0]
                    y = feature.geometry().asPoint()[1]

                    if p_mesh_idx > -1 and (type(feature[p_mesh_idx]) !=
                                            QPyNullVariant):
                        mesh_size = feature[p_mesh_idx]
                    else:
                        mesh_size = 0.1

                    line = "Point(IP+" + str(last_pid) + ") = {"
                    line = line + str(x) + ", " + str(y)
                    line = line + ", 0, " + str(mesh_size) + "};\n"
                    innerPoint_lines.append(line)
                    Attr = {'Physical': feature[p_Phx_idx],
                            'geoName': "IP+"+str(last_pid),
                            'mesh_size': feature[p_mesh_idx],
                            'Surface': feature[surf_idx],
                            'x': x, 'y': y,
                            'Attr': 'InnerPoint'}
                    pointDict.update({feature.geometry().asPoint(): Attr})
                    self.innerPointLayer.update({feature.geometry().asPoint():
                                                 Attr})

                if (p_Phx_idx > -1 and
                        type(feature[p_Phx_idx]) != QPyNullVariant):
                    if feature[p_Phx_idx] in p_Phx_list.keys():
                        p_Phx_list[feature[p_Phx_idx]].append("IP+" +
                                                              str(last_pid))
                    else:
                        p_Phx_list.update({feature[p_Phx_idx]: ["IP+" +
                                                                str(last_pid)]})
                last_pid = last_pid + 1

        self.innerPointDict = pointDict
        self.p_Phx_list = p_Phx_list
        self.last_pid = last_pid

    def writeInnerLines(self, last_pid, last_lid, line_Phx_list):
        pointDict = self.innerPointDict
        lineDict = self.innerLineDict
        innerLine_lines = list()

        lineLayers = self.lineLayers
        newAttr = [QgsField("Line_id", QVariant.Int)]
        for layer in lineLayers:
            layer.startEditing()
            layer.dataProvider().addAttributes(newAttr)
            layer.commitChanges()

        for layer in lineLayers:
            fields = layer.pendingFields()
            line_id = fields.fieldNameIndex("Line_id")
            surf_id = fields.fieldNameIndex("Surface")
            phx_id = fields.fieldNameIndex("Physical")
            mesh_id = fields.fieldNameIndex("mesh_size")
            trans_id = fields.fieldNameIndex("Transfinit")
            cell_id = fields.fieldNameIndex("Cells")
            layer.startEditing()
            last_lid = last_lid + 1
            last_pid = last_pid + 1

            for feature in layer.getFeatures():
                feature[line_id] = last_lid
                layer.updateFeature(feature)

                lineGeo = feature.geometry().asPolyline()
                for point in lineGeo:
                    if mesh_id > -1 and feature[mesh_id] is not None:
                        mesh_size = feature[mesh_id]
                    else:
                        mesh_size = 0.1

                    Attr = {"Surface": feature[surf_id],
                            "mesh_size": mesh_size,
                            "x": point.x(),
                            "y": point.y(),
                            "geoName": "IP+"+str(last_pid),
                            "Attr": 'InnerLine'}
                    pointDict.update({point: Attr})
                    last_pid = last_pid + 1

            line_Phx_Names = list()
            for i in range(0, len(line_Phx_list)):
                line_Phx_Names.append(line_Phx_list[i][0])

            for feature in layer.getFeatures():
                linePoints = list()
                for point in feature.geometry().asPolyline():
                    linePoints.append(pointDict[point]['geoName'])

                if feature['ForceBound'] == long(0):
                    linePoints = tuple(linePoints)
                    Attr = {"Surface": feature[surf_id],
                            "Physical": feature[phx_id],
                            "Transfinit": feature[trans_id],
                            "cell_id": feature[cell_id],
                            "geoName": str(last_lid)}
                    lineDict.update({linePoints: Attr})
                    self.innerLineLayer.update({linePoints: Attr})

                    if feature[phx_id] in line_Phx_Names:
                        for i in range(0, len(line_Phx_list)):
                            if line_Phx_list[i][0] == feature[phx_id]:
                                line_Phx_list[i][1].append(str(last_lid))
                            else:
                                pass
                    else:
                        line_Phx_list.append([feature[phx_id], [str(last_lid)]])

                    last_lid = last_lid + 1
                else:
                    for i in range(1, len(linePoints)):
                        newLine = (linePoints[i-1], linePoints[i])
                        Attr = {"Surface": feature[surf_id],
                                "Physical": feature[phx_id],
                                "Transfinit": feature[trans_id],
                                "cell_id": feature[cell_id],
                                "geoName": str(last_lid)}
                        lineDict.update({newLine: Attr})
                        self.innerLineLayer.update({newLine: Attr})
                        if feature[phx_id] in line_Phx_Names:
                            for i in range(0, len(line_Phx_list)):
                                if line_Phx_list[i][0] == feature[phx_id]:
                                    line_Phx_list[i][1].append(str(last_lid))
                                else:
                                    pass
                        else:
                            line_Phx_list.append([feature[phx_id],
                                                  [str(last_lid)]])
                        last_lid = last_lid + 1

        self.innerLine_lines = innerLine_lines
        self.line_Phx_list = line_Phx_list
        self.last_lid = last_lid
        self.last_pid = last_pid
        self.innerPointDict = pointDict
        self.innerLineDict = lineDict

    def genLoop(self, feature):
        emp_idx = self.emp_idx
        surf_id = self.surf_id
        mesh_id = self.mesh_id
        phx_id = self.phx_id
        loopDict = self.loopDict
        recomb_idx = self.recomb_idx
        last_pid = self.last_pid + 1
        last_lid = self.last_lid + 1
        loop_num = self.loop_num
        surface_id = self.surface_Num
        pointDict = self.innerPointDict
        lineDict = self.innerLineDict

        geom = feature.geometry().asPolygon()
        if mesh_id > -1 and type(feature[mesh_id]) != QPyNullVariant:
            mesh_size = feature[mesh_id]
        else:
            mesh_size = 0.1

        for loop in geom:
            for point in loop:
                Attr = {'mesh_size': mesh_size,
                        'Surface': feature[surf_id],
                        'geoName': "IP+"+str(last_pid), 'x': point[0],
                        'y': point[1], "Attr": 'InnerLoop'}
                pointDict.update({point: Attr})
                last_pid = last_pid + 1

            loopString = list()
            if feature['ForceBound'] == long(0):
                lineString = list()
                for point in loop:
                    lineString.append(pointDict[point]['geoName'])
                Attr = {'Surface': feature[surf_id],
                        'geoName': str(last_lid)}
                lineString = tuple(lineString)
                last_lid = last_lid + 1
                loopString.append(str(last_lid))

            else:
                for i in range(1, len(loop)):
                    point0 = loop[i-1]
                    point1 = loop[i]
                    key = tuple([pointDict[point0]['geoName'],
                                 pointDict[point1]['geoName']])
                    Attr = {'Surface': feature['Surface'],
                            'geoName': str(last_lid)}
                    lineDict.update({key: Attr})
                    loopString.append(str(last_lid))
                    last_lid = last_lid + 1

            loopName = "ILL+" + str(loop_num)
            geoName = "IS+" + str(feature[surf_id])
            loopDict[geoName].append({loopName: tuple(loopString)})
            loop_num = loop_num + 1

        if feature[emp_idx] == long(0):
            geoName = "IS+" + str(surface_id)
            self.surfaceSet.append(geoName)
            loopDict.update({geoName: [loopName]})
            if type(feature[phx_id]) != QPyNullVariant:
                if feature['Physical'] in self.physicalSurfaces.keys():
                    self.physicalSurfaces[feature['Physical']
                                          ].append('IS+' + str(surface_id))
                else:
                    self.physicalSurfaces.update({feature['Physical']:
                                                  ['IS+' + str(surface_id)]})
            if feature[recomb_idx] == long(1):
                self.recombine.update({geoName: True})
            surface_id = surface_id + 1

        self.last_lid = last_lid
        self.last_pid = last_pid
        self.loop_num = loop_num
        self.surface_Num = surface_id
        self.loopDict = loopDict
        self.innerPointDict = pointDict
        self.innerLineDict = lineDict

    def writePolygonLoops(self, loop_num):
        polyLayers = self.polygonLayers
        self.innerPlane_lines = list()
        self.surface_phx = list()
        self.innerPlane_recomb = list()
        self.loop_num = loop_num

        for layer in polyLayers:
            fields = layer.pendingFields()
            self.emp_idx = fields.fieldNameIndex("Empty")
            self.surf_id = fields.fieldNameIndex("Surface")
            self.mesh_id = fields.fieldNameIndex("mesh_size")
            self.phx_id = fields.fieldNameIndex("Physical")
            self.recomb_idx = fields.fieldNameIndex('Recombine')

            for feature in layer.getFeatures():
                self.genLoop(feature)
