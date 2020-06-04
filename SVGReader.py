from lxml import etree
import string

class Shape:

    def __init__(self, geometry):
        self.points = [] # List of tuples
        self.style = {}
        self.id = geometry.get("id")
        self.centerx = 0
        self.centery = 0
        self.minx = 0.0
        self.maxx = 0.0
        self.miny = 0.0
        self.maxy = 0.0
        self.label = ""
        self.connectionStart = ""
        self.connectionEnd = ""
        if "path" in geometry.tag: self._initFromPath(geometry.attrib)
        elif "rect" in geometry.tag: self._initFromRect(geometry.attrib)

    @staticmethod
    def _parseStyle(value):
        style = {}
        valuePairs = value.split(";")
        for valuePair in valuePairs:
            pair = valuePair.split(":")
            style[pair[0]] = pair[1]
        return style 

    @staticmethod
    def _parsePointList(value):
        points = []
        tokens = value.split(" ")
        relative = False
        for token in tokens[:-1]: # Last point repeats
            if "m" == token[0]:
                relative = True

            if "," in token: # point
                pt = token.split(",")
                points.append((float(pt[0]), float(pt[1])))

        # All points are relative to the first point
        if relative:
            (startx, starty) = points[0]
            for i in range(1, len(points)):
                x = points[i][0]+startx
                y = points[i][1]+starty
                points[i] = (x,y)
                startx = x
                starty = y
        return points

    @staticmethod
    def _parseTransform(value):
        transform = [1, 0, 0, 1, 0, 0]
        if value is not None and "matrix" in value:
            pruned = value.strip("matrix()")
            tokens = pruned.split( ",")
            transform[0] = float(tokens[0])
            transform[1] = float(tokens[1])
            transform[2] = float(tokens[2])
            transform[3] = float(tokens[3])
            transform[4] = float(tokens[4])
            transform[5] = float(tokens[5])

        if value is not None and "translate" in value:
            pruned = value.strip("translate()")
            tokens = pruned.split( ",")
            transform[4] = float(tokens[0])
            transform[5] = float(tokens[1])

        if value is not None and "scale" in value:
            pruned = value.strip("scale()")
            tokens = pruned.split( ",")
            if len(tokens) == 2:
                transform[0] = float(tokens[0])
                transform[3] = float(tokens[1])
            else: 
                transform[0] = float(pruned)
                transform[3] = float(pruned)

        return transform

    def _initFromPath(self, attributes):
        transform = [1, 0, 0, 1, 0, 0]
        for (key,value) in attributes.iteritems():
            if key == "d": self.points = Shape._parsePointList(value)
            elif key == "style": self.style = Shape._parseStyle(value)
            elif key == "transform": transform = Shape._parseTransform(value)
            elif key == "{http://www.inkscape.org/namespaces/inkscape}label": self.label = value
            elif "connection-start" in key: self.connectionStart = value
            elif "connection-end" in key: self.connectionEnd = value
            #print(key,value)
        self.applyTransform(transform)

    def isConnector(self):
        #print(self.connectionStart, self.connectionEnd)
        return self.connectionStart != "" and self.connectionEnd != ""
        
    def _initFromRect(self, attributes):
        width = 0
        height = 0
        x = 0
        y = 0
        transform = [1, 0, 0, 1, 0, 0]
        for (key,value) in attributes.iteritems():
            if key == "style": self.style = Shape._parseStyle(value)
            elif key == "width": width = float(value)
            elif key == "height": height = float(value)
            elif key == "x": x = float(value)
            elif key == "y": y = float(value)
            elif key == "transform": transform = Shape._parseTransform(value)
            elif key == "{http://www.inkscape.org/namespaces/inkscape}label": self.label = value

        self.points.append((x,y))
        self.points.append((x+width,y))
        self.points.append((x+width,y+height))
        self.points.append((x,y+height))
        self.applyTransform(transform)
        
    def __repr__(self):
        str = "%s (%s):\n"%(self.id, self.label)
        for key,value in self.style.items():
            str += "\t%s:%s\n"%(key, value)
        str += self.points.__repr__()
        str += "\n"
        return str

    def applyTransform(self, transform):
        for i in range(len(self.points)):
            p = self.points[i]
            x = transform[0] * p[0] + transform[2] * p[1] + transform[4]
            y = transform[1] * p[0] + transform[3] * p[1] + transform[5]
            self.points[i] = (x, y)
        self.initExtents()

    def getBBox(self):
        return [self.minx, self.miny, self.maxx, self.maxy]

    def getCenter(self):
        return (self.centerx, self.centery)

    def initExtents(self):
        self.minx = 999999.0
        self.miny = 999999.0
        self.maxx = -999999.0
        self.maxy = -999999.0
        for p in self.points:
            self.minx = min(p[0], self.minx)
            self.miny = min(p[1], self.miny)
            self.maxx = max(p[0], self.maxx)
            self.maxy = max(p[1], self.maxy)

        self.centerx = self.minx + 0.5*(self.maxx - self.minx)
        self.centery = self.miny + 0.5*(self.maxy - self.miny)

class SVGReader:

    def __init__(self):
        self.shapes = []
        self.root = None

    def load(self, filename, groupName = "gFloorPlan"):
        file = open(filename) 
        tree = etree.parse(file)
        file.close()

        self.root = tree.getroot()
        floorPlan = self.findGroup(self.root, groupName)
        if floorPlan is None:
            print("Warning: no '%s' group"%groupName)
            return
        self._initShapes(floorPlan)

    def computeBBox(self):
        minx = 999999.0
        miny = 999999.0
        maxx = -999999.0
        maxy = -999999.0

        for shape in self.shapes:
            bbox = shape.getBBox()
            minx = min(bbox[0], minx)
            miny = min(bbox[1], miny)
            maxx = max(bbox[2], maxx)
            maxy = max(bbox[3], maxy)

        return [minx, miny, maxx, maxy]
   
    def getShapes(self):
        return self.shapes

    def findGroup(self, root, id):
        children = list(root)
        for child in children:
            attributes = child.attrib
            if attributes.get("id") == id: return child
            descendant = self.findGroup(child, id)
            if descendant is not None: return descendant
        return None        
        
    def _initShapes(self, root):
        self.shapes = []
        geometry = list(root)

        value = root.attrib.get("transform")
        transform = Shape._parseTransform(value) 
        transform[4] = 0
        transform[5] = 0
        for geom in geometry:
            shape = Shape(geom)
            shape.applyTransform(transform)
            self.shapes.append(shape)

if __name__ == '__main__':

    reader = SVGReader()
    reader.load("foodcourt.svg") # px = ft

    for shape in reader.getShapes():
        print(shape)

