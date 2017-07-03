
from qgis.utils import iface
from qgis.core import QgsVectorFileWriter, QGis, QgsPoint
from qgis.core import QgsVectorLayer, QgsFeature, QgsFields, QgsField
from qgis.core import QgsGeometry
import os.path
from PyQt4.QtCore import QVariant, QFileInfo, QPyNullVariant


def createNewAttrs(fields):
    mesh_size_idx = fields.fieldNameIndex("mesh_size")
    FB_idx = fields.fieldNameIndex("ForceBound")
    Phx_idx = fields.fieldNameIndex("Physical")
    geo_idx = fields.fieldNameIndex("geoName")
    struct_idx = fields.fieldNameIndex("Recombine")
    trans_idx = fields.fieldNameIndex("Transfinite")
    newAttr = list()

    if mesh_size_idx == -1:
        newAttr.append(QgsField("mesh_size", QVariant.Double))
    if FB_idx == -1:
        newAttr.append(QgsField("ForceBound", QVariant.Int))
    if Phx_idx == -1:
        newAttr.append(QgsField("Physical", QVariant.String))
    if geo_idx == -1:
        newAttr.append(QgsField("geoName", QVariant.String))
    if struct_idx == -1:
        newAttr.append(QgsField("Recombine", QVariant.Int))
    if trans_idx == -1:
        newAttr.append(QgsField("Transfinite", QVariant.Int))
    return newAttr


def copyMainLayer(layer, folder):
    CRS = layer.dataProvider().crs()
    fields = layer.pendingFields()

    layerPath = layer.dataProvider().dataSourceUri().split('|')[0]
    baseName = os.path.split(layerPath)[-1].replace(".shp", '')
    path = os.path.join(folder, os.path.join('MainLayers',
                                             'Main_' + str(baseName) + '.shp'))
    if os.path.isfile(path):
        return False

    layerType = QGis.WKBPolygon
    newlayer = QgsVectorFileWriter(path, "utf-8", fields,
                                   layerType, CRS, "ESRI Shapefile")

    for feature in layer.getFeatures():
        NewFeature = QgsFeature()  # Create an empty feature
        NewFeature.setGeometry(feature.geometry())  # Set feature geometry
        NewFeature.setAttributes(feature.attributes())  # Set attributes
        #  Update feature to the new layer
        newlayer.addFeature(NewFeature)
    del newlayer

    newAttr = createNewAttrs(fields)

    newlayer = QgsVectorLayer(path, QFileInfo(path).baseName(), 'ogr')
    newlayer.startEditing()
    #  Add new attribute field to layer
    newlayer.dataProvider().addAttributes(newAttr)
    newlayer.commitChanges()

    newlayer.startEditing()
    fields = newlayer.pendingFields()
    FB_idx = fields.fieldNameIndex("ForceBound")
    Phx_idx = fields.fieldNameIndex("Physical")
    struct_idx = fields.fieldNameIndex("Recombine")
    geo_idx = fields.fieldNameIndex("geoName")
    for feature in newlayer.getFeatures():
        featId = feature.id()
        featureFields = feature.attributes()
        #  If nothing is written in field "ForceBound" and "Physical", write in
        #  1 in "ForceBound" to show force boundary in preset, and fill "Domain"
        #  in "Physical" to express the physical domain in grid generation.
        if type(featureFields[FB_idx]) == QPyNullVariant:
            attr = {FB_idx: 0}
            newlayer.dataProvider().changeAttributeValues({featId: attr})
        if type(featureFields[Phx_idx]) == QPyNullVariant:
            attr = {Phx_idx: "Domain"}
            newlayer.dataProvider().changeAttributeValues({featId: attr})
        if type(featureFields[struct_idx]) == QPyNullVariant:
            attr = {struct_idx: 1}
            newlayer.dataProvider().changeAttributeValues({featId: attr})
        if type(featureFields[geo_idx]) == QPyNullVariant:
            name = "IS+" + str(feature.id()+1)
            attr = {geo_idx: name}
            newlayer.dataProvider().changeAttributeValues({featId: attr})
    newlayer.commitChanges()

    return newlayer


def num_of_points(geometry):
    num = 0
    for i in range(0, len(geometry)):
        num = num + len(geometry[i])

    return num


def writePoints(Pointwriter, p_loops, feature, **args):
    feature_num = args['feature_num']
    id_num = args['id_num']
    units = args['units']
    num_in_polygon = args['num_in_polygon']
    mesh_size_idx = args['mesh_size_idx']
    p_units = args['p_units']

    loop_num = 0
    for points in p_loops:
        for point in points:
            pointFeature = QgsFeature()  # generate feature
            pointFeature.setGeometry(QgsGeometry.fromPoint(QgsPoint(point)))
            #  Set the geometry of feature(the points inside the points
            #  list)
            Name = ("P" + str(feature_num).zfill(units) + "L" +
                    str(loop_num).zfill(2) + "P" +
                    str(num_in_polygon).zfill(p_units))
            mesh_size = (feature[mesh_size_idx] if mesh_size_idx > -1 else 0.02)
            #  Set the attributes of feature
            pointFeature.setAttributes([id_num, Name, mesh_size, loop_num,
                                        point[0], point[1], None])

            Pointwriter.addFeature(pointFeature)

            id_num = id_num + 1
            num_in_polygon = num_in_polygon + 1
        loop_num = loop_num + 1

    return Pointwriter


def writeLines(LineWriter, p_loops, feature, **args):
    feature_num = args['feature_num']
    units = args['units']
    p_units = args['p_units']
    line_id_num = args['line_id_num']
    line_FBnd = args['line_FBnd']

    line_id = 0
    loop_num = 0
    for points in p_loops:
        for i in range(1, len(points)):
            #  Set fit-to-polygon boundary if not assigned False on
            #  ForceBoundary attribute.
            lineFeature = QgsFeature()  # generate feature
            #  Set the geometry of feature(line: point-point)
            lineFeature.setGeometry(QgsGeometry.fromPolyline([points[i-1],
                                                              points[i]]))
            l_Name = ("P" + str(feature_num).zfill(units) + "L" +
                      str(loop_num).zfill(2) + "L" +
                      str(line_id).zfill(p_units))

            Start_p = (line_id_num)
            End_p = (line_id_num+1)
            #  Attributes of feature
            lineFeature.setAttributes([line_id_num, l_Name, loop_num,
                                      line_id, Start_p, End_p, line_FBnd, None])
            LineWriter.addFeature(lineFeature)
            line_id_num = line_id_num + 1
            line_id = line_id + 1

        #  Append the last line to layer(last point--starting point)
        lineFeature = QgsFeature()
        lineFeature.setGeometry(QgsGeometry.fromPolyline([points[-1],
                                                          points[0]]))
        l_Name = ("P" + str(feature_num).zfill(units) + "L" +
                  str(loop_num).zfill(2) + "L" +
                  str(line_id).zfill(p_units))
        Start_p = line_id_num
        End_p = line_id_num - len(points) + 1
        lineFeature.setAttributes([line_id_num, l_Name, loop_num, line_id,
                                   Start_p, End_p, line_FBnd, None])
        LineWriter.addFeature(lineFeature)

        line_id_num = line_id_num + 1
        line_id = line_id + 1
        loop_num = loop_num + 1

    return LineWriter, line_id


def pointAndLine(polygonLayer, projFolder):
    #  Get the Attribute of "mesh_size " from polygon layer imported
    fields = polygonLayer.pendingFields()
    mesh_size_idx = fields.fieldNameIndex("mesh_size")
    FB_idx = fields.fieldNameIndex("ForceBound")

    #  Attributes fields of the point features
    p_fields = QgsFields()
    p_fields.append(QgsField("id", QVariant.Int))
    p_fields.append(QgsField("Name", QVariant.String))
    p_fields.append(QgsField("mesh_size", QVariant.Double))
    p_fields.append(QgsField("Loop", QVariant.Int))
    p_fields.append(QgsField("X", QVariant.Double))
    p_fields.append(QgsField("Y", QVariant.Double))
    p_fields.append(QgsField("Physical", QVariant.String))

    savePath_point = os.path.join(projFolder,
                                  os.path.join('MainLayers',
                                               "polygon-points.shp"))
    Pointwriter = QgsVectorFileWriter(savePath_point, "utf-8", p_fields,
                                      QGis.WKBPoint, None, "ESRI Shapefile")

    #  Attributes field of the line layers
    l_fields = QgsFields()
    l_fields.append(QgsField("id", QVariant.Int))
    l_fields.append(QgsField("Name", QVariant.String))
    l_fields.append(QgsField("Loop", QVariant.Int))
    l_fields.append(QgsField("Line_id", QVariant.Int))
    l_fields.append(QgsField("Start_p", QVariant.Int))
    l_fields.append(QgsField("End_p", QVariant.Int))
    #  Force boundary True is pre-set, the grid-zone must fit the polygon
    #  boundary set in the original polygon layer.
    #  Using Boolean value for boundary attribute field is not supported, thus
    #  0 and 1 is used for False and True. (0 = False, 1 = True)
    l_fields.append(QgsField("ForceBound", QVariant.Int))
    l_fields.append(QgsField("Physical", QVariant.String))

    savePath_line = os.path.join(projFolder, os.path.join('MainLayers',
                                                          "polygon-line.shp"))
    LineWriter = QgsVectorFileWriter(savePath_line, "utf-8", l_fields,
                                     QGis.WKBLineString, None, "ESRI Shapefile")

    if Pointwriter.hasError() != QgsVectorFileWriter.NoError:
        print "Error when creating shapefile: ", Pointwriter.errorMessage()
    if LineWriter.hasError() != QgsVectorFileWriter.NoError:
        print "Error when creating shapefile: ", LineWriter.errorMessage()

    id_num = 0
    feature_num = 0
    line_id_num = 0

    units = len(str(polygonLayer.featureCount()))
    polygon_info = dict()
    """dict to reference the total number of points and lines inside a
    polygon."""

    #  From the target shapefile layer, cycle through the features to read its
    #  geometery(Assumed polygon layer)
    for feature in polygonLayer.getFeatures():
        #  Read the geometry of feature from polygons in target layer(polygon)
        polygonGeometry = feature.geometry().asPolygon()
        num_in_polygon = 0  # id of the polygon

        #  Loop through all loops inside a polygon
        p_loops = list()
        for i in range(0, len(polygonGeometry)):
            _points = polygonGeometry[i]
            points = list()
            points.append(polygonGeometry[i][0])
            #  There may be repetitive points in polygon, remove the repetive
            #  points before output into shapefile
            #  Build one empty list, and copy the non-repetitive points into the
            #  list
            for j in range(1, len(polygonGeometry[i])):
                #  If the point is not on the same position with previous point,
                #  copy the point to the new point geometry list
                if not _points[j] == _points[j-1]:
                    points.append(_points[j])
            #  For a polygon, the last point is repetitive with the first point,
            #  remove the last point to make sure no repetitive points in the
            #  list.
            if points[-1] == points[0]:
                points.pop(-1)

            p_loops.append(points)
            #  The loops inside a polygon(If many loops inside a polygon).

        p_units = len(str(num_of_points(polygonGeometry)))

        #  Build-up the point layer
        Pointwriter = writePoints(Pointwriter, p_loops, feature,
                                  feature_num=feature.id(),
                                  units=units, num_in_polygon=num_in_polygon,
                                  mesh_size_idx=mesh_size_idx,
                                  id_num=id_num, p_units=p_units)

        if FB_idx > -1 and feature[FB_idx] == 0:
            line_FBnd = 0
        else:
            line_FBnd = 1

        #  Build-up the line layer
        LineWriter, line_id = writeLines(LineWriter, p_loops, feature,
                                         line_FBnd=line_FBnd,
                                         feature_num=feature.id(), units=units,
                                         p_units=p_units,
                                         line_id_num=line_id_num)

        loop_num = len(p_loops)
        #  Update the polygon_info dict
        polygon_info.update({str(feature_num).zfill(units):
                            {'points': num_of_points(polygonGeometry),
                             'lines': line_id+1, 'loops': loop_num}})

    #  Delete the shapefile writer and writes into vector layer
    del Pointwriter
    #  Load the created point layer into qgis
    del LineWriter
    #  Load the created line layer into qgis
    pointLayer = QgsVectorLayer(savePath_point,
                                QFileInfo(savePath_point).baseName(),
                                'ogr')
    lineLayer = QgsVectorLayer(savePath_line,
                               QFileInfo(savePath_line).baseName(),
                               'ogr')
    return pointLayer, lineLayer


def run(polygonLayer, projFolder):
    #  Shape file loader
    newPolygonLayer = copyMainLayer(polygonLayer, projFolder)

    source = newPolygonLayer.dataProvider().dataSourceUri().split('|')[0]
    #  Load the assinged shape file layer into qgis, and show on the canvas.
    iface.addVectorLayer(source, QFileInfo(source).baseName(), 'ogr')

    pointLayer, lineLayer = pointAndLine(newPolygonLayer, projFolder)

    return newPolygonLayer, pointLayer, lineLayer
