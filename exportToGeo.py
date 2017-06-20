
from qgis.core import QgsVectorLayer
from PyQt4.QtCore import QFileInfo, QPyNullVariant, QProcess
from PyQt4.QtCore import QProcessEnvironment
from operator import itemgetter
from innerLayers import innerLayersExport


point_List = list()
lines_List = list()


class fileWriter:
    def __init__(self, writer):

        self.totalSurface = 0  # Total number of features in base polygon layer

        self.f = writer
        self.mainPointList = list()
        self.mainLineList = list()
        self.surfaceSet = list()

        self.innerPointDict = dict()
        self.innerLineDict = dict()
        self.innerPointLayer = dict()
        self.innerLineLayer = dict()

        self.mainLoopList = list()
        self.mainSurfaceList = list()
        self.loopDict = dict()
        self.loopLines = list()
        self.innerSurfaceList = list()
        self.innerSurface_Phx = list()

        self.physicalPoints = dict()
        self.physicalLines = dict()
        self.physicalSurfaces = list()
        self.physicalList = list()

        self.mainSurfaceLine = list()

        self.recombine = dict()
        self.recombineList = list()
        self.innerPlane_recomb = list()
        self.innerList = list()
        self.innerFeatureLines = list()
        self.TransLineList = list()
        self.TransSurface = ""

    def writeLineLoop(self, f):
        loopDict = self.loopDict
        for key in sorted(loopDict.keys()):
            if type(loopDict[key]) == list:
                for loop in loopDict[key]:
                    if type(loop) == dict:
                        for name in loop:
                            lineString = "Line Loop(" + name + ") = {"
                            for line in loop[name]:
                                lineString = lineString + line + ", "
                            lineString = lineString[:-2] + "};\n"
                            f.write(lineString)
        f.write('\n')
        return f

    def genSurface(self):
        loopDict = self.loopDict

        for surface in sorted(loopDict.keys()):
            loop_list = loopDict[surface]
            loopString = "Plane Surface(" + surface + ") = {"
            for loop in loop_list:
                if type(loop) == dict:
                    for item in loop:
                        loopString = loopString + str(item) + ", "
                elif type(loop) == str:
                    loopString = loopString + str(loop) + ", "

            loopString = loopString[:-2] + "};\n"
            self.mainSurfaceLine.append(loopString)
            if self.recombine[surface]:
                line = "Recombine Surface{" + surface + "};\n"
                self.recombineList.append(line)

    def arrangeInnerLineString(self, head, List, tail):
        String = head
        for item in List:
            String = String + item + ", "
        String = String[:-2] + "} In Surface{" + tail + "};\n"
        return String

    def arangeInnerList(self):
        surfaceSet = self.surfaceSet
        innerPointDict = self.innerPointLayer
        pointInSurface = list()
        if innerPointDict:
            point_in_feature = list()
            for surface in surfaceSet:
                for key in innerPointDict.keys():
                    if "IS+" + str(innerPointDict[key]['Surface']) == surface:
                        point_in_feature.append(innerPointDict[key]['geoName'])
            if point_in_feature:
                String = self.arrangeInnerLineString("Point{", point_in_feature,
                                                     surface)
                pointInSurface.append(String)
        self.pointInSurface = pointInSurface

        innerLineDict = self.innerLineLayer
        lineInSurface = list()
        if innerLineDict:
            line_in_feature = list()
            for surface in surfaceSet:
                for key in innerLineDict.keys():
                    if "IS+" + str(innerLineDict[key]['Surface']) == surface:
                        line_in_feature.append(innerLineDict[key]['geoName'])
                if line_in_feature:
                    String = self.arrangeInnerLineString("Line{",
                                                         line_in_feature,
                                                         surface)
                    lineInSurface.append(String)
        self.lineInSurface = lineInSurface

    def physicalPointsArange(self):
        if self.physicalPoints:
            for key in sorted(self.physicalPoints.keys()):
                line = "Physical Point('" + key + "') = {"
                for name in sorted(self.physicalPoints[key]):
                    line = line + name + ", "
                line = line[:-2] + "};\n"
                self.physicalList.append(line)

    def physicalLinesArange(self):
        if self.physicalLines:
            for i in range(0, len(self.physicalLines)):
                line = "Physical Line('" + self.physicalLines[i][0] + "') = {"
                for ids in sorted(self.physicalLines[i][1]):
                    line = line + ids + ", "
                line = line[:-2] + "};\n"
                self.physicalList.append(line)

    def writePhysicalSurfaces(self, f):
        if self.physicalSurfaces:
            for key in sorted(self.physicalSurfaces.keys()):
                lineString = "Physical Surface('" + key + "') = {"
                for item in self.physicalSurfaces[key]:
                    lineString = lineString + item + ", "
                lineString = lineString[:-2] + "};\n"
                f.write(lineString)
            f.write('\n')
        return f

    def writeInnerPoint(self, f):
        if self.innerPointDict:
            for point in sorted(self.innerPointDict.values(),
                                key=itemgetter('geoName')):
                pointString = ("Point(" + point['geoName'] + ") = {" +
                               str(point['x']) + ", " + str(point['y']) +
                               "0, " + str(point["mesh_size"]) + "};\n")
                f.write(pointString)
            f.write('\n')
        return f

    def writeInnerLine(self, f):
        innerLineDict = self.innerLineDict
        if self.innerLineDict:
            lineList = list()
            for key in innerLineDict.keys():
                lineList.append([key, innerLineDict[key]['geoName'],
                                innerLineDict[key]])
            lineList = sorted(lineList, key=itemgetter(1))
            for line in lineList:
                lineString = "Line(" + line[1] + ") = {"
                for point in line[0]:
                    lineString = lineString + point + ", "
                lineString = lineString[:-2] + "};\n"
                f.write(lineString)
            f.write('\n')
        return f

    def writeInnerSurface(self, f):
        if self.innerSurfaceList:
            for line in self.innerSurfaceList:
                f.write(line)
            f.write('\n')
        return f

    def writeInnersAbout(self, f):
        if self.pointInSurface:
            for line in self.pointInSurface:
                f.write(line)
        if self.lineInSurface:
            for line in self.lineInSurface:
                f.write(line)
            f.write('\n')
        return f

    def writeTransfinite(self, f):
        if self.TransLineList:
            for line in self.TransLineList:
                f.write(line)
            f.write('\n')
        if self.TransSurface:
            f.write(self.TransSurface)
        return f

    def removeRepetitive(self):
        mainPoints = self.mainPointList
        mainPoints = set(mainPoints)
        self.mainPointList = list(mainPoints)
        self.mainPointList = sorted(self.mainPointList)

        mainLines = self.mainLineList
        mainLines = set(mainLines)
        self.mainLineList = list(mainLines)
        self.mainLineList = sorted(self.mainLineList)

    def write(self):

        self.removeRepetitive()

        f = self.f
        for line in self.mainPointList:
            f.write(line)
        f.write('\n')

        f = self.writeInnerPoint(f)

        for line in self.mainLineList:
            f.write(line)
        f.write('\n')

        f = self.writeInnerLine(f)

        f = self.writeLineLoop(f)

        self.arangeInnerList()
        self.physicalPointsArange()
        self.physicalLinesArange()
        self.genSurface()

        for line in self.mainSurfaceLine:
            f.write(line)
        f.write('\n')

        #  Write innerList data
        f = self.writeInnerSurface(f)

        f = self.writeInnersAbout(f)

        for line in self.physicalList:
            f.write(line)
        f.write('\n')

        f = self.writePhysicalSurfaces(f)

        for line in self.recombineList:
            f.write(line)
        f.write('\n')

        f = self.writeTransfinite(f)

        f.close()


def writeLines(innerPoints, innerLines, pointPhx, linePhx, innerPointPhx,
               innerLinePhx, fileWriter):
    for line in point_List:
        fileWriter.write(line)
    for line in innerPoints:
        fileWriter.write(line)

    fileWriter.write('\n')

    for line in lines_List:
        fileWriter.write(line)
    for line in innerLines:
        fileWriter.write(line)

    fileWriter.write('\n')

    return fileWriter


#  Seperate the boundary of each polygon(surface)
def check_line_bnd(line_attr, l_Name_idx, FBnd_idx):
    for i in range(0, len(line_attr)):
        line_attr[i][l_Name_idx] = line_attr[i][l_Name_idx].split('L')[0]
    sorted(line_attr, key=itemgetter(l_Name_idx))


def seperateLoops(AllLines):
    _AllLines = list()

    for group in AllLines:
        Loop_in_group = list()
        for i in range(0, len(group)):
            Loop_in_group.append(int(group[i][1].split('L')[1]))

    #  Find number of loops in line group.
    #  Use a list to contain the loop number of all lines, then remove the
    #  repetitive number
        loops = list()  # Loops inside a line-group
        loop = Loop_in_group[0]
        loops.append(loop)
        for line in Loop_in_group:
            if not line == loop:
                loop = line
                loops.append(loop)

        _loops = list()
        for i in range(0, len(loops)):
            line_group = list()
            for line in group:
                if int(line[1].split('L')[1]) == loops[i]:
                    line_group.append(line)
            _loops.append(line_group)
        _AllLines.append(_loops)

    return _AllLines


def forceBoundary(polyLayer):
    polyFields = polyLayer.pendingFields()
    #  Fields in polygon-layer
    poly_FBnd = polyFields.fieldNameIndex('ForceBound')

    FBnd_ref = dict()
    poly_num = 0
    units = len(str(polyLayer.featureCount()))
    for feature in polyLayer.getFeatures():
        key = 'P' + str(poly_num).zfill(units)
        if poly_FBnd > -1:
            if feature[poly_FBnd] == 0:
                FBnd_ref.update({key: False})
            else:
                FBnd_ref.update({key: True})
        else:
            FBnd_ref.update({key: True})
        poly_num = poly_num + 1

    return FBnd_ref


def pointPhx(pointList):
    if not pointList:
        return dict()
    _pointList = list()
    for point in pointList:
        if type(point) == list and type(point[1]) != QPyNullVariant:
            _pointList.append(point)

    if not _pointList:
        return dict()

    pointList = _pointList

    pointList = sorted(pointList, key=itemgetter(1))

    #  Get the types of physical points
    Phxlist = list()
    item = pointList[0][1]
    Phxlist.append(pointList[0][1])
    for point in pointList:
        if not item == point[1]:
            item = point[1]
            Phxlist.append(point[1])

    physPoint = dict()
    for i in range(0, len(Phxlist)):
        typePoints = list()
        for point in pointList:
            if point[1] == Phxlist[i]:
                typePoints.append(point[0])
        physPoint.update({Phxlist[i]: typePoints})

    return physPoint


def linePhxIdx(lineList):
    # Build a dict with input list, if list contains
    lineSet = set(lineList)

    linePhxDict = dict()
    for attr in lineSet:
        linePhxDict.update({attr: []})

    return linePhxDict


def pointWriter(pointFrameLayer):

    pointFields = pointFrameLayer.pendingFields()
    #  Fields in point-layer
    mesh_size_idx = pointFields.fieldNameIndex("mesh_size")
    p_Phx_idx = pointFields.fieldNameIndex("Physical")
    p_Name_idx = pointFields.fieldNameIndex('geoName')

    #  from the point layer, write the points declaration into GMSH script
    #  {X, Y, Z=0, mesh_size} mesh_size is retrived from attribute field of
    #  points-layer.
    PhyPointList = list()
    last_pid = 0
    for feature in pointFrameLayer.getFeatures():
        x = feature.geometry().asPoint()[0]
        y = feature.geometry().asPoint()[1]
        line = ("Point(" + feature[p_Name_idx] + ') = {' + str(x) + ', ' +
                str(y) + ', 0, ' + str(feature[mesh_size_idx]) + '};\n')
        point_List.append(line)

        if p_Phx_idx > -1 and type(feature[p_Phx_idx]) != QPyNullVariant:
            PhyPointList.append([feature['geoName'],
                                 feature[p_Phx_idx]])

        last_pid = last_pid + 1

    if PhyPointList:
        PhyPointList = pointPhx(PhyPointList)
        for key in PhyPointList.keys():
            line = "Physical Point('" + key + "') = {"
            for name in PhyPointList[key]:
                line = line + name + ", "
            line = line[:-2]
            line = line + "};\n"

    return last_pid, pointPhx(PhyPointList)


class surfaceWriter:
    def __init__(self, polygonLayer, loopList, **args):
        self.mainLoopLine = list()
        self.mainSurfaceLine = list()
        self.recombineList = list()
        self.physicalSurface = list()
        self.polygonLayer = polygonLayer
        self.loopList = loopList

        self.recombineGrid()

        if 'inner' in args.keys():
            self.innerFeatures = args['inner']
        else:
            self.innerFeatures = dict()

        surfaceSet = list()
        poly_fields = polygonLayer.pendingFields()
        phx_idx = poly_fields.fieldNameIndex("Physical")
        name_idx = poly_fields.fieldNameIndex("geoName")

        self.phx_idx = phx_idx
        self.name_idx = name_idx

        Phx_list = list()
        for feature in polygonLayer.getFeatures():
            surfaceSet.append(feature['geoName'])
            if phx_idx > -1 and type(feature[phx_idx]) != QPyNullVariant:
                Phx_list.append([feature[name_idx], feature[phx_idx]])

        if Phx_list:
            Phx_list = pointPhx(Phx_list)

        self.Phx_list = Phx_list
        self.surfaceSet = surfaceSet

        #  Consider each polygon is a physical surface, the lines from a polygon
        #  must build-up a loop
        self.surface_writeLoops()
        self.TransfiniteSurface()

    def recombineGrid(self):
        polygonLayer = self.polygonLayer
        fields = polygonLayer.pendingFields()
        rc_idx = fields.fieldNameIndex('Recombine')
        recombine = dict()
        for feature in polygonLayer.getFeatures():
            polykey = feature['geoName']
            if rc_idx == -1 or type(feature[rc_idx]) == QPyNullVariant:
                recombine.update({polykey: False})
            elif rc_idx > -1 and feature[rc_idx] == 0:
                recombine.update({polykey: False})
            else:
                recombine.update({polykey: True})
        self.recombine = recombine

    def surface_writeLoops(self):
        loop_list = self.loopList

        loop_num = 0
        for surface in sorted(loop_list.keys()):
            loops = loop_list[surface]
            for loop in loops:
                for item in loop:
                    lines_in_loop = loop[item]
                    loopString = "Line Loop(" + item + ") = {"
                    for line in lines_in_loop:
                        loopString = loopString + line + ", "
                    loopString = loopString[:-2] + "};\n"
                    self.mainLoopLine.append(loopString)
                    loop_num = loop_num + 1

        self.loop_num = loop_num

    def TransfiniteSurface(self):
        polygonLayer = self.polygonLayer

        empty = True
        line = "Transfinite Surface{"
        for feature in polygonLayer.getFeatures():
            if type(feature['Transfinit']) != QPyNullVariant:
                if int(feature['Transfinit']) == 1:
                    line = line + feature['geoName'] + ', '
                    empty = False
        line = line[:-2] + "};"

        if not empty:
            self.Transfinite = line
        else:
            self.Transfinite = ""


class lineWriter:
    def __init__(self, lineFrameObj):
        #  Fields in line-layer
        lineFields = lineFrameObj.frameLayer.pendingFields()
        self.l_Name_idx = lineFields.fieldNameIndex("geoName")
        self.l_FB_idx = lineFields.fieldNameIndex("ForceBound")
        self.l_Phx_idx = lineFields.fieldNameIndex("Physical")
        self.trn_idx = lineFields.fieldNameIndex("Transfinit")
        self.cell_idx = lineFields.fieldNameIndex("Cells")
        self.lineFrame = lineFrameObj
        self.pointDict = lineFrameObj.pointDict

        self.getLinesFromLayer()
        self.TransfiniteLines()

    def getLinesFromLayer(self):
        lineLayer = self.lineFrame.frameLayer
        pointDict = self.pointDict
        l_Name_idx = self.l_Name_idx

        Phx_lines = list()

        for feature in lineLayer.getFeatures():
            geo = feature.geometry().asPolyline()
            _geo = feature.geometry().asMultiPolyline()
            if geo:
                geoName = feature[l_Name_idx]
                line = "Line(" + geoName + ") = {"
                for point in geo:
                    line = line + pointDict[point]['geoName'] + ", "
                line = line[:-2] + "};\n"
                lines_List.append(line)
            elif _geo:
                geoName = feature[l_Name_idx]
                line = "Line(" + geoName + ") = {"
                line = line + pointDict[_geo[0][0]]['geoName'] + ", "
                for i in range(0, len(_geo)):
                    for j in range(1, len(_geo[i])):
                        line = line + pointDict[_geo[i][j]]['geoName'] + ", "
                line = line[:-2] + "};\n"
                lines_List.append(line)

        allPhysicLines = list()
        for feature in lineLayer.getFeatures():
            if feature['Physical']:
                allPhysicLines.append((feature['Physical'], feature['seq']))
        allPhysicLines = set(allPhysicLines)
        allPhysicLines = list(allPhysicLines)
        allPhysicLines = sorted(allPhysicLines, key=itemgetter(1))

        Phx_lines = list()
        for i in range(0, len(allPhysicLines)):
            Phx_lines.append([allPhysicLines[i][0], []])

        for feature in lineLayer.getFeatures():
            if feature['Physical']:
                for j in range(0, len(Phx_lines)):
                    if feature['Physical'] == Phx_lines[j][0]:
                        Phx_lines[j][1].append(feature['geoName'])

        self.Phx_lines = Phx_lines

    def TransfiniteLines(self):
        lineLayer = self.lineFrame.frameLayer
        Trans_list = dict()
        Trans_cells_num = list()
        Trans_lines = list()
        for feature in lineLayer.getFeatures():
            if (type(feature['Cells']) != QPyNullVariant and
                    feature['Cells'] != long(0)):
                Trans_cells_num.append(feature['Cells'])
        Trans_cells_num = set(Trans_cells_num)

        for cell_num in Trans_cells_num:
            Trans_list.update({cell_num: []})
            for feature in lineLayer.getFeatures():
                if type(feature['Cells']) != QPyNullVariant:
                    if feature['Cells'] == cell_num:
                        Trans_list[cell_num].append(feature['geoName'])

        for cell_num in Trans_list:
            line = "Transfinite Line{"
            for name in Trans_list[cell_num]:
                line = line + name + ", "
            line = line[:-2] + "} = " + str(cell_num) + ";\n"
            Trans_lines.append(line)

        self.TransLines = Trans_lines


def genGeo(projFolder, polyLayer, pointFrameLayer, lineFrameObj, loopList,
           geoPath):
    #  pointLayerPath: absolute path to the shape file of lines from
    #  polygon layer.
    #  lineLayerPath: absolute path to the shapefile of points from
    #  polygon layer.
    #  geoPath: absolute path to the output .geo file

    #  Open .geo GMSH script file
    #  Header, the total length of variable and formats seem to be limited.
    f = open(geoPath, 'w')

    f.write('IP = newp;\n')
    f.write('ILL = newll;\n')
    f.write('IS = news;\n')

    #  get the attribute fields from vector layers

    #  Use the name of attribute fields, get the index of desired attribute.
    #  (the attribute field was build in newPointLayer, filled while exporting
    #  polygon-layer.)

    #  Write Points into GMSH script
    last_pid, p_Phx_list = pointWriter(pointFrameLayer)

    #  Write lines to GMSH script, from line in line-layer, which is exported
    #  from polygon-layer.

    lines = lineWriter(lineFrameObj)
    Phxlines = lines.Phx_lines

    last_lid = lineFrameObj.frameLayer.featureCount()-1

    innerList = innerLayersExport(projFolder, polyLayer)
    innerList.openLayers()
    innerList.run()
    innerList.writeInnerPoints(last_pid, p_Phx_list)
    innerList.writeInnerLines(innerList.last_pid, last_lid, Phxlines)
    innerFeatures = pointPhx(innerList.inner_list)

    #  Write surface(polygon) definiteion into GMSH script
    Surfaces = surfaceWriter(polyLayer, loopList, inner=innerFeatures)

    innerList.loopDict = Surfaces.loopList
    innerList.recombine = Surfaces.recombine
    innerList.physicalSurfaces = Surfaces.Phx_list
    innerList.writePolygonLoops(Surfaces.loop_num)

    fw = fileWriter(f)
    fw.totalSurface = polyLayer.featureCount()

    fw.loopDict = innerList.loopDict
    fw.mainPointList = point_List
    fw.mainLineList = lines_List
    fw.surfaceSet = Surfaces.surfaceSet
    fw.innerPointDict = innerList.innerPointDict
    fw.innerLineDict = innerList.innerLineDict
    fw.physicalPoints = innerList.p_Phx_list
    fw.physicalLines = innerList.line_Phx_list
    fw.physicalSurfaces = innerList.physicalSurfaces
    fw.innerSurfaceList = innerList.innerPlane_lines
    fw.innerSurface_Phx = innerList.surface_phx
    fw.innerPointLayer = innerList.innerPointLayer
    fw.innerLineLayer = innerList.innerLineLayer
    fw.recombine = innerList.recombine
    fw.innerPlane_recomb = innerList.innerPlane_recomb
    fw.TransLineList = lines.TransLines
    fw.TransSurface = Surfaces.Transfinite
    fw.write()

    f.close()
    del fw
