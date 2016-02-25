from ij import IJ, ImagePlus, ImageStack
from ij.io import FileSaver
from sys import argv
from os import path
from ij.measure import ResultsTable as RT

def main():
    checkArgs(argv)
    makeStack(argv[1])
    applyFilter(argv[1]+"/stack.tif")
    straighten(argv[1]+"/stack-filtered(Li).tif")

def applyFilter(stackName):
    imp = IJ.openImage(stackName)
    stack = imp.getImageStack()

    for i in xrange(1, imp.getNSlices()+1):
        image = ImagePlus(str(i), stack.getProcessor(i))
        IJ.run(image, "Auto Threshold", "method=Li white")

        #IJ.run(image, "Analyze Particles...", "size= 1000-Infinity circularity=0.00-1.00 show=Masks in_situ")
    imp2 = ImagePlus("Threshold", stack)
    fs = FileSaver(imp2)
    print "Saving filtered stack"
    fs.saveAsTiff(stackName[:-4] + "-filtered(Li).tif")

def straighten(stackName):
    imp = IJ.openImage(stackName)
    stack = imp.getImageStack()

    for i in xrange(1, imp.getNSlices()+1):
        image = ImagePlus(str(i), stack.getProcessor(i))
        xvals = []
        yvals = []
        maxvals = []
        j = 0

        for k in xrange(0, 512, 2):
            #IJ.run(image, "makeRectangle", ")
            IJ.makeRectangle(i, 0, 4, 512)
            IJ.run("Measure")
            table = RT.getResultsTable()
            print "\n\n", table

            #x = IJ.getResult("XM")
            #y = IJ.getResult("YM")
            #maxi = IJ.getResult("Max")

            #xvals.append(k)
            #yvals.append(y)
            #maxvals.append(maxi)

            #if maxvals[j] == 0 and j > 0:
            #    yvals[j] = yvals[j-1]

            #j += 1

        IJ.makeSelection("freeline", xvals, yvals)
        IJ.run("Straighten...", "line = 80")


def makeStack(stackDir, stackName = "stack"):
    IJ.run("Image Sequence...", "open="+stackDir+" file = (img) sort")
    imp = IJ.getImage()
    #IJ.run("8-bit")
    fs = FileSaver(imp)
    print "Saving stack"
    fs.saveAsTiff(stackDir + "/" +stackName+".tif")

def checkArgs(argv):
    """Checks for a valid directory"""
    if len(argv) != 2:
        print "Usage: applyThreshold_.py folder"
        exit(0)

    stackDir = argv[1]
    if not path.exists(stackDir) or not path.isdir(stackDir):
        print "Invalid directory"
        exit(0)


if __name__ == "__main__":
    main()
