"""
Julian Segert, Bio119. Preliminary testing for Fiji scripting
"""

from ij import IJ, ImagePlus, ImageStack
from ij.io import FileSaver
from sys import argv




stackDir = argv[1]
#IJ.run("Image Sequence...", "open="+stackDir+" sort")
imp = IJ.openImage(stackDir+"/stack.tif")
stack = imp.getImageStack()
print "Number of slices:", imp.getNSlices()

for i in xrange(1, imp.getNSlices()):
    print i
    image = stack.getProcessor(i)
    IJ.run(ImagePlus(str(i), image), "Auto Threshold", "method=Default white")

imp2 = ImagePlus("Threshold", stack)
fs = FileSaver(imp2)
fs.saveAsTiff(stackDir + "/Filtered.tif")


"""
#in case you want to make a stack from a folder
imp = IJ.getImage()
#stack = imp.getImageStack()

fs = FileSaver(imp)
fs.saveAsTiff(stackDir + "/stack.tif")


#print "Number of slices:", stack.getNSlices()

#imp = IJ.openImage(argv[1]) #first command line arg is file directory
#print imp.title
"""
