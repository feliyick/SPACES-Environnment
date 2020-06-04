from SVGReader import *
import sys

#**************************************************************************
#*   Code: pointInPoly()                                                   *
#* Author: Jeremy Winston                                                  *
#*   Date: 09/04/97 Thu                                                    *
#*                                                                         *
#* Description:                                                            *
#*   Implements the odd-even test for deciding if a point lies within a    *
#* polygon.  pointInPoly() casts a ray from the point (x,y) to infinity    *
#* parallel to the X axis, and counts the number of edges of the polygon,  *
#* p, that the ray intersects.  If the number of edges intersected is odd, *
#* then (x,y) lies withing p.  If the number of edges intersected is even, *
#* then (x,y) lies outside of p.                                           *
#*                                                                         *
#* ASN: Port to Python                                                     *
#***************************************************************************/
    
def pointInPoly(x, y, polygonX, polygonY): # polygon is list of pairs (x,y)
    numOfCrossings = 0		 # Count of poly's edges crossed */
    vCt = 0			         # Vertex counter */
    numVerts = len(polygonX)

    x1 = polygonX[-1]	             # Start with the last edge of p */
    y1 = polygonY[-1]

    def checkCrossings(vCt, numOfCrossings, x1, y1):
        # For each edge e of polygon p, see if the ray from (x,y) to (infinity,y)
        # crosses e:
        x2 = polygonX[vCt];
        y2 = polygonY[vCt];

        # If y is between (y1,y2] (e's y-range),
        # and (x,y) is to the left of e, then
        #     the ray crosses e:
        if ((((y2<=y) and (y<y1)) or ((y1<=y) and (y<y2)))
                and (x < (x1 - x2) * (y - y2) / (y1 - y2) + x2)):
            numOfCrossings = numOfCrossings+1

        x1 = x2
        y1 = y2
        vCt = vCt+1

        return vCt, numOfCrossings, x1, y1

    (vCt, numOfCrossings, x1, y1) = checkCrossings(vCt, numOfCrossings, x1, y1)
    while (vCt < numVerts): 
        (vCt, numOfCrossings, x1, y1) = checkCrossings(vCt, numOfCrossings, x1, y1)

    return numOfCrossings % 2

def InsidePolygon(px, py, points):
    polygonX = [x for (x,y) in points]
    polygonY = [y for (x,y) in points]
    return pointInPoly(px, py, polygonX, polygonY)

def Cross(x1,y1, x2,y2):
    return x1 * y2 - x2 * y1

def IsConvex(p0,p1,p2):
    x2 = p0[0] - p1[0]
    y2 = p0[1] - p1[1]
    x1 = p1[0] - p2[0]
    y1 = p1[1] - p2[1]
    if Cross(x1, y1, x2, y2) > 0: # counter clockwise
       return True
    return False

def CacheEars(points):
    results = [] # list of boolean: true -> convex

    num = len(points)
    for i in range(num): results.append(False)

    for i in range(num):
        p0 = points[(i+0)%num]
        p1 = points[(i+1)%num]
        p2 = points[(i+2)%num]

        if IsConvex(p0,p1,p2):
            results[(i+1)%num] = True
            tri = [p0, p1, p2]
            for p in points:
                if p == p0 or p == p1 or p == p2: continue
                if InsidePolygon(p[0], p[1], tri):
                    results[(i+1)%num] = False
    return results

def ClipEar(points):
    if len(points) == 3:
        return (points, [])

    ears = CacheEars(points)
    #print "----------------------"
    #print len(points)
    #for i in range(len(points)): 
        #print "%0.2f,%0.2f"%(points[i][0],points[i][1]), ears[i]

    num = len(points)
    for i in range(num):
        p0 = points[(i+0)%num]
        p1 = points[(i+1)%num]
        p2 = points[(i+2)%num]

        isEar = ears[(i+1)%num]
        if isEar:
           triangle = [p0, p1, p2]
           poly = points
           poly.remove(p1)
           return (triangle, poly)
           #return ([], poly)

    #print "WARNING", len(points), points
    return ([], [])

def CheckPointList(points):
    correct = 0
    incorrect = 0
    num = len(points)
    for i in range(num):
        p0 = points[(i+0)%num]
        p1 = points[(i+1)%num]
        p2 = points[(i+2)%num]

        if IsConvex(p0,p1,p2):
            correct = correct + 1
        else:
            incorrect = incorrect + 1

    #print correct, incorrect, len(points)
    return correct > incorrect

def GetTriangleList(points):
    if not CheckPointList(points):
        points.reverse()

    triangles = []
    (tri, poly) = ClipEar(points)
    if len(tri) > 0: triangles.append(tri)
    while len(poly) > 0:
        (tri, poly) = ClipEar(poly)
        if len(tri) == 0: continue
        triangles.append(tri)

    return triangles

class SVG2TXTExporter:

    def __init__(self, reader):
        self.reader = reader

        # Center map
        bbox = self.reader.computeBBox()
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        x = bbox[0]+width/2
        y = bbox[1]+height/2
        transform = [1, 0, 0, 1, -x, -y]

        for shape in self.reader.getShapes():
            shape.applyTransform(transform)

        bbox = self.reader.computeBBox()

    def Export(self):
        for i in range(len(self.reader.getShapes())):
            line = self.GetDataString(i)
            if line != "": print line
            
    def GetDataString(self, shapeId):
        shape = self.reader.getShapes()[shapeId]
        color = shape.style.get("fill", "#000000")
        if color == "none": return ""

        # Convert polygons into triangle lists
        # using simple ear splitting technique
        line = ""
        points = list(shape.points)
        if len(points) == 0:
           #print "ERROR: Empty shape", shape.id, shape.label
           return ""

        points.reverse()
        triangles = GetTriangleList(points)
        for tri in triangles:
           line += "%.2f,%.2f "%(tri[0][0], tri[0][1])
           line += "%.2f,%.2f "%(tri[1][0], tri[1][1])
           line += "%.2f,%.2f "%(tri[2][0], tri[2][1])

        line += "/ "
        for p in shape.points:
            line += "%.2f,%.2f "%(p[0], p[1])
        line += "%.2f,%.2f "%(shape.points[0][0], shape.points[0][1])
        
        return "%s %s"%(color, line)

if __name__ == '__main__':    

    filename = "foodcourt.svg"
    try:
        if len(sys.argv) > 1:
            for i in range(1, len(sys.argv)):
                filename = sys.argv[i]
    except:
        print "usage: python SVG2TXT.py <svg_filename>"
    
    reader = SVGReader()
    reader.load(filename)

    writer = SVG2TXTExporter(reader)
    writer.Export()

