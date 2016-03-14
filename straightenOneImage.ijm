macro "Straighten" {

    run("Set Measurements...", "  center min redirect=None decimal=1");

    roi_windowsize = 1;
    num_points = 512/roi_windowsize;
    xvals = newArray(num_points);
    yvals = newArray(num_points);
    maxvals=newArray(num_points);

    counter = 0;
    for (i=0; i<512; i+=roi_windowsize) {
    	makeRectangle(i, 0, roi_windowsize, 512);
    	run("Measure");
    	x=getResult("XM"); //get the last result by omitting the second argument
    	y=getResult("YM");
        max=getResult("Max");

    	xvals[counter]=i + roi_windowsize/2;
    	yvals[counter]=y;
        maxvals[counter]= max;

    	// if the roi falls off the end of the root the max value should drop to 0 if the threshold was set correctly
    	if((maxvals[counter]==0) && (counter>0)) { //set position to last good position
    		yvals[counter]=yvals[counter-1];
    	}

    	//Use this overlay to see where the midline is being called
    	//Overlay.drawRect(i, yvals[counter], 4, 4);
    	//Overlay.show;

    	counter++;
    }

    makeSelection("freeline", xvals, yvals);
    run("Straighten...", "line=80");

}
