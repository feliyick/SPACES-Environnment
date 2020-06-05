from SVGReader import *
import sys, math

if __name__ == '__main__':    

    filename = "pachacamacSiteMap.svg"
    try:
        if len(sys.argv) > 1:
            for i in range(1, len(sys.argv)):
                filename = sys.argv[i]
    except:
        print("usage: python SVG2TXT.py <svg_filename>")
    
    reader = SVGReader()
    reader.load(filename, "layer1") # Reads floor plan

    # Step 1: Center
    bbox = reader.computeBBox()
    #print(bbox)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = bbox[0]+width/2
    y = bbox[1]+height/2
    transform = [1, 0, 0, 1, -x, -y]

    for shape in reader.getShapes():
        shape.applyTransform(transform)

    bbox = reader.computeBBox()
    #print(bbox)

    # Step 2: Export
    for shape in reader.getShapes():

        if len(shape.points) == 0: continue

        color = shape.style.get("fill", "#000000")

        cmd = "curve -name curve_%s -d 1 "%(shape.label)
        for p in shape.points:
            cmd += "-p %f %f %f "%(p[0], 0, p[1])

        index = 0
        for p in shape.points:
            cmd += "-k %d "%index
            index = index + 1

        print(cmd,";")

        # test
        for i in range(len(shape.points)-1):
            p0 = shape.points[i]
            p1 = shape.points[i+1]
            dx = p1[0]-p0[0]
            dz = p1[1]-p0[1]
            centerx = (p1[0]+p0[0])*0.5
            centerz = (p1[1]+p0[1])*0.5
            angle = math.atan2(dx, dz) * 180/math.pi + 90 

            width = math.sqrt(dx*dx + dz*dz)
            depth = 0.25 # size of other wall dimensions
            height = 0.25 # size of other wall dimensions
            print("polyCube -w %f -h %f -d %f -sx 1 -sy 1 -sz 1 -ax 0 1 0 -cuv 4 -ch 1;"%(width,height,depth))
            print("move -a %f %f %f;"%(centerx, 0, centerz))
            print("rotate -a %f %f %f;"%(0, angle, 0))
      

#curve -d 1 -p -1.040225 0 0.0477602 -p -1.040225 0 -3.974931 -p 0.971121 0 -3.974931 -p 0.971121 0 0.0477602 -p -0.946674 0 0.0945357 -k 0 -k 1 -k 2 -k 3 -k 4 -name wallCurve;
#setAttr "wallCurve.rotateX" 90;
#extrude -ch true -rn false -po 1 -et 2 -ucp 1 -fpt 1 -upn 1 -rotation 0 -scale 1 -rsp 1 "wallCurve" "curve1" ;

