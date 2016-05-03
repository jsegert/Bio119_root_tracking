"""
Takes the directory of a series of images and creates a new directory
containing straightened images.
"""
from ij import IJ
from sys import argv, exit
from os import path, mkdir
from ij.io import FileSaver, DirectoryChooser
from ij import WindowManager as wm
from ij.gui import GenericDialog
import shutil
from ij.measure import ResultsTable as RT
from time import sleep
import math
from ij.plugin.frame import RoiManager
from ij.measure import CurveFitter
from trainableSegmentation import WekaSegmentation
from trainableSegmentation import Weka_Segmentation
from ij import ImagePlus

def main():
    userDir = DirectoryChooser("Choose a folder")
    imgDir = userDir.getDirectory()
    import_and_straighten(imgDir)
    measure_growth(imgDir)

def measure_growth(imgDir, filename = "Fiji_Growth.txt"):
    """ Collects measurement data in pixels and writes to a file. Uses straightened binary images"""
    f = open(imgDir + filename, 'w')
    f.write("Img number\tEnd point (pixels)\n")
    IJ.run("Set Measurements...", "area mean min center redirect=None decimal=3")
    index = "000000000"
    filename = imgDir + "/binary" + "/img_" + index + "__000-padded.tif"
    while path.exists(filename):
		imp = IJ.openImage(filename)
		imp.show()
		IJ.run("Clear Results")
		for i in xrange(800): #hard coded to target length for now
			IJ.makeRectangle(i, 0, 1, 80)
			IJ.run("Measure")
			table = RT.getResultsTable()
			#print "i:", i, "counter:", table.getCounter()
			maxi = RT.getValue(table, "Max", i)
			if maxi == 0:
				f.write(str(int(index)) + "\t" + str(i) + "\n")
				break

		IJ.runMacro("while (nImages>0) {selectImage(nImages);close();}")
		index = to_9_Digits(str(int(index)+1))
		filename = imgDir + "/padded" + "/img_" + index + "__000-padded.tif"
    f.close()


def import_and_straighten(imgDir):
    """
    Core function. Opens images in given directory in series and calls a straightening function.
    Thresholds using weka if stddev of pixel intensities is too high (bright field), otherwise uses
    histogram based segmentation.
    """
    targetWidth = 800 #adjustable
    make_directory(imgDir)
    index = "000000000"
    filename = imgDir + "/img_" + index + "__000.tif"
    if path.exists(filename):
        weka = Weka_segmentor(IJ.openImage(filename))
    while path.exists(filename):
        IJ.run("Set Measurements...", "mean standard min center redirect=None decimal=3")
        IJ.run("Clear Results")
        imp = IJ.openImage(filename)
        imp.show()
        IJ.run("Rotate 90 Degrees Left")
        IJ.run("Measure")
        table = RT.getResultsTable()
        stddev = RT.getValue(table, "StdDev", 0)

        if stddev < 20:
            segmented = weka.getThreshold(imp)
            segmented.show()
            IJ.run("8-bit")
            IJ.run("Invert")
            imp.close()
            imp = segmented

        else:
            IJ.run(imp, "Auto Threshold", "method=Li white") #threshold

        imp = preProcess_(imp)

        #straighten_roi_rotation()
        coords = run_straighten()

        newImp = IJ.getImage()
        """
        fs = FileSaver(newImp)
        fs.saveAsTiff(imgDir + "/straightened" + "/img_" + index + "__000-straight.tif")
        """

        IJ.run("Image Padder", "pad_right="+str(targetWidth - newImp.getWidth()))
        paddedImp = IJ.getImage()
        fs = FileSaver(paddedImp)
        fs.saveAsTiff(imgDir + "/binary" + "/img_" + index + "__000-padded.tif")

        IJ.runMacro("while (nImages>0) {selectImage(nImages);close();}")

        #use same centerline for original greyscale image
        imp = IJ.openImage(filename)
        imp.show()
        IJ.run("Rotate 90 Degrees Left")
        IJ.run("8-bit")
        IJ.runMacro("makeLine("+coords+")")
        IJ.run("Straighten...", "line = 80")
        newImp = IJ.getImage()
        IJ.run("Image Padder", "pad_right="+str(targetWidth - newImp.getWidth()))
        paddedImp = IJ.getImage()
        IJ.run("8-bit")
        fs = FileSaver(paddedImp)
        fs.saveAsTiff(imgDir + "/greyscale" + "/img_" + index + "__000-padded.tif")
        IJ.runMacro("while (nImages>0) {selectImage(nImages);close();}")

        index = to_9_Digits(str(int(index)+1))
        filename = filename = imgDir + "/img_" + index + "__000.tif"


def preProcess_(imp):
    """ Noise filtering step. Removes particles other than the root after segmentation.
    Takes a pointer to an ImagePlus, returns pointer to new ImagePlus. """
    IJ.runMacro("//setThreshold(1, 255);")
    IJ.runMacro("run(\"Convert to Mask\");")
    IJ.run("Analyze Particles...", "size=400-Infinity show=Masks")
    filteredImp = IJ.getImage()
    #imp.close()
    #IJ.run("Invert")
    IJ.run("Invert LUT")
    return filteredImp

def run_straighten(roiWindowsize = 4):
    """ Original straightening function based on Nick's macro. Used in final version.
    Returns coordinate string used to make centerline. """
    IJ.run("Set Measurements...", "mean min center redirect=None decimal=3")
    IJ.runMacro("//setTool(\"freeline\");")
    IJ.run("Line Width...", "line=80");
    numPoints = 512/roiWindowsize
    xvals = []
    yvals = []
    maxvals = []
    counter = 0

    for i in range(0, 512, roiWindowsize):
        IJ.run("Clear Results")
        IJ.makeRectangle(i, 0, roiWindowsize, 512)
        IJ.run("Measure")
        table = RT.getResultsTable()
        xvals.append(i + roiWindowsize/2)
        yvals.append(RT.getValue(table, "YM", 0))
        maxvals.append((RT.getValue(table, "Max", 0)))

        if maxvals[counter] == 0 and counter > 0:
            yvals[counter] = yvals[counter - 1]

        counter += 1

    coords = ""
    for i in range(numPoints - 1):
        coords += str(xvals[i]) + ", " + str(yvals[i]) +", "
    coords += str(xvals[numPoints-1]) + ", " + str(yvals[numPoints-1])

    IJ.runMacro("makeLine("+coords+")")
    IJ.run("Straighten...", "line = 80")
    return coords



def straighten_roi_rotation(roiWindowsize = 8):
    """ Root straightening function that rotates ROI to follow root slope.
    Does not work properly.
    """
    IJ.run("Set Measurements...", "mean standard min center redirect=None decimal=3")
    IJ.runMacro("//setTool(\"freeline\");")
    IJ.run("Line Width...", "line=80");
    #numPoints = 512/roiWindowsize
    xvals = []
    yvals = []
    maxvals = []
    counter = 0
    maxIters = 800/roiWindowsize
    minIters = 10

    imp = IJ.getImage().getProcessor()

    rm = RoiManager()
    if find_first_pixel(0,imp) == None or find_last_pixel(0,imp)[1] == None:
        return
    y = (find_first_pixel(0,imp)[1]+find_last_pixel(0,imp)[1])/2
    roi = roiWindow_(imp, center = (roiWindowsize/2,y), width = roiWindowsize, height = 512)
    xvals.append(roiWindowsize/2)
    yvals.append(y)
    maxvals.append(0)
    roi.findTilt_()
    i = 0
    while i < maxIters and roi.containsRoot_():
    	roi.advance_(roiWindowsize)
        IJ.run("Clear Results")
        IJ.run("Measure")
        table = RT.getResultsTable()

        x  = RT.getValue(table, "XM", 0)
        y = RT.getValue(table, "YM", 0)
        if imp.getPixel(int(x),int(y)) != 0:
            xvals.append(x)
            yvals.append(y)
            maxvals.append((RT.getValue(table, "Max", 0)))


        #roi.advance_(roiWindowsize)
        print "here"
        roi.unrotateRoot_()
        IJ.run("Clear Results")
        IJ.run("Measure")
        roi.restoreCenter_(RT.getValue(table, "XM", 0), RT.getValue(table, "YM", 0))
        #exit(1)
        sleep(.5)
        roi.findTilt_()
        i += 1
    coords = ""
    for i in range(len(xvals)-1):
        coords += str(xvals[i]) + ", " + str(yvals[i]) +", "
    coords += str(xvals[len(xvals)-1]) + ", " + str(yvals[len(xvals)-1])

    IJ.runMacro("makeLine("+coords+")")
    IJ.run("Straighten...", "line = 80")


def find_last_pixel(x, ip):
    """ Helper function to find slope. Returns last non-zero point in given x dimension."""
    for i in range(512, 0, -1):
		pix = ip.getPixel(x,i)
		#print "pix:", pix
		if pix == 255.0:
			#print x, i
			return (x,i)
    return None

def find_first_pixel(x, ip):
    """ Helper function to find slope. Returns first non-zero point in given x dimension."""
    for i in range(512):
		pix = ip.getPixel(x,i)
		#print "pix:", pix
		if pix == 255.0:
			#print x, i
			return (x,i)
    return None

def straighten_with_centerpoints(roiWindowsize = 4):
    """ Failed straightening method utilizing ROI rotation. """
    IJ.run("Set Measurements...", "mean min center redirect=None decimal=3")
    IJ.runMacro("//setTool(\"freeline\");")
    IJ.run("Line Width...", "line=80");
    numPoints = 512/(roiWindowsize)
    xvals = []
    yvals = []
    maxvals = []

    imp = IJ.getImage().getProcessor()

    for i in range(0, 512, roiWindowsize):
        topLeft = find_first_pixel(i, imp)
        bottomLeft = find_last_pixel(i, imp)
        #print "topLeft:", topLeft, "bottomLeft:", bottomLeft
        #sleep(.2)

        if not topLeft == None and not bottomLeft == None:
            xvals.append(i)
            yvals.append((topLeft[1] + bottomLeft[1])/2)

        topRight = find_first_pixel(i + roiWindowsize, imp)
        bottomRight = find_last_pixel(i + roiWindowsize, imp)

        if not topRight == None and not bottomRight == None:
            xvals.append(i + roiWindowsize)
            yvals.append((topRight[1] + bottomRight[1])/2)

    coords = ""
    #print "xvals:", xvals
    #print "yvals:", yvals
    for i in range(len(xvals)-1):
        coords += str(xvals[i]) + ", " + str(yvals[i]) +", "
    coords += str(xvals[len(xvals)-1]) + ", " + str(yvals[len(xvals)-1])

    IJ.runMacro("makeLine("+coords+")")
    IJ.run("Straighten...", "line = 80")

def find_slope(first, second):
    """ Returns slope of the interval between first and second x coords"""
	#print first, second
    imp = IJ.getImage()
    ip = imp.getProcessor()#.convertToFloat() # as a copy
	#pixels = ip.getPixels()
	#if first == 0: print pixels
    first_pixel = find_first_pixel(first, ip)
    second_pixel = find_first_pixel(second, ip)
    if first_pixel == None or second_pixel == None:
	       return 0

    return ((float(first_pixel[1])-second_pixel[1])/(first_pixel[0]-second_pixel[0]))

def to_9_Digits(num):
    """ Helper function for iterating over images. Pads index to 9 digits with high-order zeros."""
    if len(num) > 9:
        print "Index overflow"
        exit(1)

    return "0"*(9 - len(num)) + num


def make_directory(imgDir):
    """ Makes the necessary output directories or overwrites current ones. """
    if not path.exists(imgDir) or not path.isdir(imgDir):
        print "Not a valid directory"
        exit(0)

    if not path.exists(imgDir+"/binary"):
        mkdir(imgDir+"/binary")

    else:
    	gd = GenericDialog("Confirm Overwrite")
    	choices = ["Yes", "No"]
    	gd.addChoice("Overwrite \"binary\" folder?", choices, choices[0])
    	gd.showDialog()
    	if gd.wasCanceled():
    		exit(0)
    	choice = gd.getNextChoice()
    	if choice == "No":
    		exit(0)
    	shutil.rmtree(imgDir+"/binary")
    	mkdir(imgDir+"/binary")


    if not path.exists(imgDir+"/greyscale"):
        mkdir(imgDir+"/greyscale")

    else:
    	gd = GenericDialog("Confirm Overwrite")
    	choices = ["Yes", "No"]
    	gd.addChoice("Overwrite \"greyscale\" folder?", choices, choices[0])
    	gd.showDialog()
    	if gd.wasCanceled():
    		exit(0)
    	choice = gd.getNextChoice()
    	if choice == "No":
    		exit(0)
    	shutil.rmtree(imgDir+"/greyscale")
    	mkdir(imgDir+"/greyscale")

def get_root_points(imp, startX, endX, startY = 0, endY = 512):
    """ Returns lists of corresponding x and y values that contain non-zero pixels in
    a given interval """
    xVals = []
    yVals =[]
    for x in range(startX, endX):
        for y in range(startY, endY):
            if imp.getPixel(x, y) == 255:
                xVals.append(x)
                yVals.append(y)
    return xVals, yVals

def get_regression(xVals, yVals):
    """ Runs a linear regression on x and y values and returns slope """
    cf = CurveFitter(xVals, yVals)
    cf.doFit(0) #linear
    return cf.getParams()[1]

class Weka_segmentor(object):
    """ Wrapper class for trainable Weka segmentation. """
    def __init__(self, imp, classifier = "/Users/juliansegert/repos/Bio119_root_tracking/bright.model"):
        self.imp = imp
        self.classifier = classifier

        self.segmentor = WekaSegmentation(self.imp)
        self.segmentor.loadClassifier(self.classifier)

    def getThreshold(self, imp):
        result = ImagePlus(imp.title, self.segmentor.applyClassifier(imp).getProcessor())
        return result



class roiWindow_(object):
    """ Class to encapsulate moving ROI in straighten_roi_rotation.  """
    def __init__(self, imp, center = (0,0), width = 0, height = 0, tilt = 0):
       	#self.RoiM = RoiManager()
        self.imp = imp
        self.center = center
        self.width = width
        self.height = height
        self.tilt = tilt
        self.dTheta = 0
        print self.center

        self.roi = IJ.makeRectangle(center[0] - width/2, center[1] - height/2, width, height)
        #IJ.runMacro("roiManager(\"Add\");")
        #IJ.runMacro("roiManager(\"Select\", 0);")
        #IJ.run("Rotate...", "angle =" + str(self.tilt))
        #sleep(60)

    def findTilt_(self):
        #self.tilt = find_slope(int(self.center[0] - (math.cos(math.radians(self.tilt)) * self.width/2)), int(self.center[0] + (math.cos(math.radians(self.tilt)) * self.width/2)))
        points = get_root_points(self.imp,int(self.center[0] - self.width/2), int(self.center[0] + self.width/2))
        self.tilt = -math.degrees(math.atan(get_regression(points[0], points[1])))

    def translate_(self, dx, dy):
        IJ.runMacro("roiManager(\"translate\", " +str(dx) + ", " + str(dy) + ")")
        self.center = (self.center[0] + dx, self.center[1] +dy)
        #self.RoiM.translate(dx, dy)
        #IJ.runMacro("roiManager(\"translate\", 4, 4)")


    def rotate_(self): # dTheta):
        IJ.runMacro("run(\"Rotate...\",\"  angle=" +str(self.dTheta)+"\");")

    def advance_(self, dist):
        prevTilt = self.tilt
        #print "prev tilt", prevTilt
        xDist = math.cos(math.radians(self.tilt)) * dist #probably wrong
        yDist = -math.sin(math.radians(self.tilt)) * dist
        print "x, y dist: ", xDist, yDist
        self.translate_(xDist, yDist)
        self.findTilt_()
        print "tilt: ", self.tilt
        self.dTheta = prevTilt-self.tilt
        self.rotate_() #(prevTilt - self.tilt)

    def containsRoot_(self):
        IJ.run("Clear Results")
        IJ.run("Measure")
        table = RT.getResultsTable()
        if RT.getValue(table, "Max", 0) == 0:
            return False
        return True

    def restoreCenter_(self,x,y):
    	#print "before centering: ", x, y, self.center
        dx = x-self.center[0]
        dy = y-self.center[1]
        self.translate_(dx,dy)

        print "restore center", dx, dy, self.center

    def unrotateRoot_(self): # dTheta):
		IJ.runMacro("run(\"Rotate...\",\"  angle=" +str((-1)*self.dTheta)+"\");")


if __name__ == "__main__":
    main()
