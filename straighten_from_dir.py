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

def main():
    userDir = DirectoryChooser("Choose a folder")
    imgDir = userDir.getDirectory()
    import_and_straighten(imgDir)


def import_and_straighten(imgDir):
    targetWidth = 800 #adjustable
    make_directory(imgDir)
    index = "000000000"
    filename = imgDir + "/img_" + index + "__000.tif"
    while path.exists(filename):
        imp = IJ.openImage(filename)
        IJ.run(imp, "Auto Threshold", "method=Li white") #threshold
        imp.show()
        IJ.runMacroFile("/Users/juliansegert/repos/Bio119_root_tracking/straightenOneImage.ijm")
        newImp = IJ.getImage()
        fs = FileSaver(newImp)
        fs.saveAsTiff(imgDir + "/straightened" + "/img_" + index + "__000-straight.tif")

        IJ.run("Image Padder", "pad_right="+str(targetWidth - newImp.getWidth()))
        paddedImp = IJ.getImage()
        fs = FileSaver(paddedImp)
        fs.saveAsTiff(imgDir + "/padded" + "/img_" + index + "__000-padded.tif")

        IJ.run("Close All Windows")


        index = to_9_Digits(str(int(index)+1))
        filename = filename = imgDir + "/img_" + index + "__000.tif"



def to_9_Digits(num):
    if len(num) > 9:
        print "Index overflow"
        exit(1)

    return "0"*(9 - len(num)) + num


def make_directory(imgDir):
    if not path.exists(imgDir) or not path.isdir(imgDir):
        print "Not a valid directory"
        exit(0)

    if not path.exists(imgDir+"/straightened"):
        mkdir(imgDir+"/straightened")

    else:
    	gd = GenericDialog("Confirm Overwrite")
    	choices = ["Yes", "No"]
    	gd.addChoice("Overwrite \"straightened\" folder?", choices, choices[1])
    	gd.showDialog()
    	if gd.wasCanceled():
    		exit(0)
    	choice = gd.getNextChoice()
    	if choice == "No":
    		exit(0)
    	shutil.rmtree(imgDir+"/straightened")
    	mkdir(imgDir+"/straightened")
    	

    if not path.exists(imgDir+"/padded"):
        mkdir(imgDir+"/padded")

    else:
    	gd = GenericDialog("Confirm Overwrite")
    	choices = ["Yes", "No"]
    	gd.addChoice("Overwrite \"padded\" folder?", choices, choices[1])
    	gd.showDialog()
    	if gd.wasCanceled():
    		exit(0)
    	choice = gd.getNextChoice()
    	if choice == "No":
    		exit(0)
    	shutil.rmtree(imgDir+"/padded")
    	mkdir(imgDir+"/padded")




if __name__ == "__main__":
    main()
