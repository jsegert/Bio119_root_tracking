from ij import IJ, ImagePlus, ImageStack
from ij.io import FileSaver
from sys import argv
from os import path

def main():
    checkArgs(argv)
    makeStack(argv[1])
    applyFilter(argv[1]+"/stack.tif")

def applyFilter(stackName):
    imp = IJ.openImage(stackName)
    stack = imp.getImageStack()

    for i in xrange(1, imp.getNSlices()+1):
        image = stack.getProcessor(i)
        IJ.run(ImagePlus(str(i), image), "Auto Threshold", "method=Default white")
    imp2 = ImagePlus("Threshold", stack)
    fs = FileSaver(imp2)
    fs.saveAsTiff(stackName[:-4] + "-filtered.tif")


def makeStack(stackDir, stackName = "stack"):
    IJ.run("Image Sequence...", "open="+stackDir+" file = (.tif) sort")
    imp = IJ.getImage()
    fs = FileSaver(imp)
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

main()
