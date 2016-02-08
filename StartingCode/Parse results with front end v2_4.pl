#!/usr/bin/perl 
    use Tk;
#   use strict;

#in next version get rid of inputs apart from list format

#Get the file to process

my $mw = MainWindow->new;
my $types=[['ImageJ result files (.xls)','.xls'],['All Files','*']];
my $file=$mw->getOpenFile(-filetypes=>$types);
print "Opening $file\n";
open(RESULTS, $file) or die "Could not open $file\n";
$mw->destroy;

#read in the ImageJ result file

#assume 12 bits and 512x512 images with starting positions of 0
$minpixel=4095;
$minden=1000000000000000;
$minpos=100000;

my %output;

while (<RESULTS>) {
	($line, $label, $min, $max, $intden, $rawden, $slice)=split;
	#skip the header line
	next if ($line=~/Label/);
	$label=~/Pos(\d*)/;
	$pos=$1;
	#make sure $pos is treated as a number
	$pos=$pos+0;
	$data{$pos}{$slice}=[$min, $max, $intden];
	#print "Found pos $pos slice $slice\n";
	#print $data{$pos}{$slice}[0]." is the min\n";
	#print $data{$pos}{$slice}[1]." is the max\n";
	#print $data{$pos}{$slice}[2]." is the integrated density\n";
	
	#assume the first position is 0
	$maxpos=$pos if ($pos>$maxpos);
	$minpos=$pos if ($minpos>$pos);
	$numpos=$maxpos-$minpos;

	#assume all positions have the same number of slices
	$slicenum=$slice if ($slice>$slicenum);
	
	#find the global min and max values
	if ($max>$maxpixel) {
		$maxpixel=$max;
		$maxpixelpos=$pos;
		$maxpixelslice=$slice;
		}
	if ($min<$minpixel) {
		$minpixel=$min;
		$minpixelpos=$pos;
		$minpixelslice=$slice;
		}
	if ($intden>$maxden) {
		$maxden=$intden;
		$maxdenpos=$pos;
		$maxdenslice=$slice;
		}
	if ($intden<$minden) {
		$minden=$intden;
		$mindenpos=$pos;
		$mindenslice=$slice;
		}
	}

print "Found $numpos positions (min $minpos, max $maxpos). Each has $slicenum slices.\n";
print "Global values:\n"; 
print "Max pixel \t$maxpixel \t\tfound at position \t$maxpixelpos slice \t$maxpixelslice\n";
print "Min pixel \t$minpixel \t\tfound at position \t$minpixelpos slice \t$minpixelslice\n";
#print "Max intden \t$maxden \tfound at position \t$maxdenpos slice \t$maxdenslice\n";
#print "Min intden \t$minden \tfound at position \t$mindenpos slice \t$mindenslice\n";

close(RESULTS);

#Get the positions to process as either averages or single slices

$mw = MainWindow->new;

$mw->Label(-text => 'First root')->pack;
my $first = $mw->Entry(-width => 4);
$first->pack;

$mw->Label(-text => 'Last root')->pack;
my $last = $mw->Entry(-width => 4);
$last->pack;

$mw->Button(
    -text => 'Average and SD',
    -command => sub{averages($first, $last)}
)->pack;

$mw->Button(
    -text => 'Single roots',
    -command => sub{singles($first, $last)}
)->pack;

$mw->Label(-text => 'Complex series (example 3,4,10-14,16,19-30 - no spaces!)')->pack;
my $complex_entry = $mw->Entry(-width => 100);
$complex_entry->pack;

$mw->Button(
    -text => 'Complex series average and SD',
    -command => sub{complex($complex_entry)}
)->pack;

$mw->Button(
    -text => 'Process',
    -command => sub{$mw->destroy}
)->pack;

MainLoop;

sub averages {
    my ($first, $last) = @_;
	my $first_val = $first->get;
    my $last_val = $last->get;
    print "Average value and SD for roots $first_val to $last_val\n";
	summarize($first_val,$last_val);
}

sub singles {
    my ($first, $last) = @_;
	my $first_val = $first->get;
    my $last_val = $last->get;
    print "Single value for roots $first_val to $last_val\n";
	for ($a=$first_val;$a<=$last_val ;$a++) {
	summarize($a,$a);
	}
}

sub complex {
	my $list=@_[0]->get;
	my @pos_list=split(',',$list);
	my @single_list;
	my $newname;

	foreach (@pos_list) {
		
		if ($_ =~/-/) {
			my ($first, $last) = split('-',$_);
			print "Found $first and $last as a pair\n";
			#make sure that the first position is smaller than the second
			if ($first>$last) {
				die "Halting: order the list of positions you want to analyze ($first is bigger than $last)\n" ;
			}
			for (my $x=$first; $x<=$last; $x++) {
			push(@single_list, $x);
			}
		}

		else {
			#print "This one $_ does not\n";
			push(@single_list, $_);
		}
	}
	
	print "Complex series for roots ";
	foreach (@single_list) {
		print $_.", ";
		$newname.=$_."_";
	}
	print "\n";
	summarize_set($newname, \@single_list);
}

my $mw = MainWindow->new;

my $types=[['Comma separated values for opening in Excel)','.csv'],['All Files','*']];
my $file=$mw->getSaveFile(-filetypes=>$types, -defaultextension => '.csv');
print "Saving to $file\n";
open(OUT, ">$file") or die "Could not open $file\n";
$mw->destroy;
report();
print "Done\n";

#subroutine to report averages and sd for a range of positions (including a single position) in a format that works for excel
sub summarize {
	my($first, $last)=@_;

	#make sure that the first position is smaller than the second
	if ($first>$last) {
		die "Halting: order the list of positions you want to analyze ($first is bigger than $last)\n" ;
	}

	my $positions=$last-$first+1;

	if ($positions > 1) {
		$name="$first-$last";
	}
	else {
		$name="$first";
	}

	print "Processing $name which is $positions positions\n";

	#initialize the arrays - without this there are problems when calculating averages for multiple groups unless each group has the same number of roots imaged
	my @pixvalues=();
	my @denvalues=();

	#now extract the data and put them in an output hash
	#step through each slice
	for (my $curslice=1; $curslice<=$slicenum; $curslice++) {
		#step through each position
		my $poscount=0;
		for (my $curpos=$first; $curpos<=$last ;$curpos++) {
			#check that this data exists
			die "Halting: position $curpos slice $curslice does not exist\n" unless (exists $data{$curpos}{$curslice});
			$pixvalues[$poscount]=$data{$curpos}{$curslice}[1];
			$denvalues[$poscount]=$data{$curpos}{$curslice}[2];
			$poscount++;
			}
		
		#now calculate stats if more than one slice
		if ($positions>1) {
				$pixave=average(\@pixvalues);
				$denave=average(\@denvalues);
				$pixsd=stdev(\@pixvalues);
				$densd=stdev(\@denvalues);
				#print "slice $curslice pixels $pixave +/- $pixsd, den $denave +/- $densd\n";
				#use this format if including integrated density
				#$output{$name}{$curslice}=[$pixave, $pixsd, $denave, $densd];
				#use this format for max pixel values only
				$output{$name}{$curslice}=[$pixave, $pixsd];
		}
		#if it is a single slice set sd to -1
		else {
				#print "slice $curslice pixels ".$pixvalues[0]." +/- 0, den ".$denvalues[0]." +/- 0\n";
				#use this format if including integrated density
				#$output{$name}{$curslice}=[$pixvalues[0], 0, $denvalues[0], 0];
				#use this format for max pixel values only
				$output{$name}{$curslice}=[$pixvalues[0], -1];
		}
	}
}

#subroutine to report averages and sd for a range of positions (including a single position) in a format that works for excel
sub summarize_set {
	my ($name, $list) = @_;
	
	my @local_list=@$list;

	my $positions=0;

	foreach (@local_list) {
		$positions++;
	}
	
	print "Processing $name which is $positions positions\n";

	#initialize the arrays - without this there are problems when calculating averages for multiple groups unless each group has the same number of roots imaged
	my @pixvalues=();
	my @denvalues=();

	#now extract the data and put them in an output hash
	#step through each slice
	for (my $curslice=1; $curslice<=$slicenum; $curslice++) {
		#step through each position
		my $poscount=0;
		foreach $curpos(@local_list) {
			#check that this data exists
			die "Halting: position $curpos slice $curslice does not exist\n" unless (exists $data{$curpos}{$curslice});
			$pixvalues[$poscount]=$data{$curpos}{$curslice}[1];
			$denvalues[$poscount]=$data{$curpos}{$curslice}[2];
			$poscount++;
			}
		
		#now calculate stats if more than one slice
		if ($positions>1) {
				$pixave=average(\@pixvalues);
				$denave=average(\@denvalues);
				$pixsd=stdev(\@pixvalues);
				$densd=stdev(\@denvalues);
				#print "slice $curslice pixels $pixave +/- $pixsd, den $denave +/- $densd\n";
				#use this format if including integrated density
				#$output{$name}{$curslice}=[$pixave, $pixsd, $denave, $densd];
				#use this format for max pixel values only
				$output{$name}{$curslice}=[$pixave, $pixsd];
		}
		#if it is a single slice set sd to -1
		else {
				#print "slice $curslice pixels ".$pixvalues[0]." +/- 0, den ".$denvalues[0]." +/- 0\n";
				#use this format if including integrated density
				#$output{$name}{$curslice}=[$pixvalues[0], 0, $denvalues[0], 0];
				#use this format for max pixel values only
				$output{$name}{$curslice}=[$pixvalues[0], -1];
		}
	}
}

#write the results to a file or stdout
sub report {

	#initialize the first column of the output
	$lines[0]="slice";
	for (my $curslice=1; $curslice<=$slicenum; $curslice++) {
		$lines[$curslice]=$curslice;
		}
	
	foreach $group (sort(keys %output)) {
	#add each group to the header line
	#use this format if using integrated denisty
	#$lines[0].="\t".$group."_maxpixel\t".$group."_pixsd\t".$group."_den\t".$group."_densd";
	
	#is this a single slice
	if ($output{$group}{1}[1] == -1) {
		$single=1;
	}
	else {
		$single=0;
	}

	#use this format for max pixel values only
	if ($single) {
		$lines[0].=",".$group."_maxpixel";
	}
	else {
		$lines[0].=",".$group."_maxpixel,".$group."_pixsd";
	}

	#add data by stepping through each position
	for (my $curslice=1; $curslice<=$slicenum; $curslice++) {
		#use this format if using integrated denisty
		#$lines[$curslice].="\t".$output{$group}{$curslice}[0]."\t".$output{$group}{$curslice}[1]."\t".$output{$group}{$curslice}[2]."\t".$output{$group}{$curslice}[3];
		#use this format for max pixel values only
		if ($single) {
			$lines[$curslice].=",".$output{$group}{$curslice}[0];
		}
		else {
			$lines[$curslice].=",".$output{$group}{$curslice}[0].",".$output{$group}{$curslice}[1];
		}

		#print $lines[$curslice]."\n";
		}
	} 

	#now print it all out
	for (my $curslice=0; $curslice<=$slicenum; $curslice++) {
		print OUT $lines[$curslice]."\n";
		}
}

#from http://edwards.sdsu.edu/labsite/index.php/kate/302-calculating-the-average-and-standard-deviation
sub average{
        my($data) = @_;
        if (not @$data) {
                die("Empty array\n");
        }
        my $total = 0;
        foreach (@$data) {
                $total += $_;
        }
        my $average = $total / @$data;
        return $average;
}
sub stdev{
        my($data) = @_;
        if(@$data == 1){
                return 0;
        }
        my $average = &average($data);
        my $sqtotal = 0;
        foreach(@$data) {
                $sqtotal += ($average-$_) ** 2;
        }
        my $std = ($sqtotal / (@$data-1)) ** 0.5;
        return $std;
}