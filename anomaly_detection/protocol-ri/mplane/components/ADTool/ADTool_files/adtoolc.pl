#!/usr/bin/perl

# ANOMALY DETECTION TOOL (ADTool) - main
#
# FTW - fiadino@ftw.at
# 

# debugging
use Log::Message::Simple qw /debug/;
use constant V  => 1; # verbouse

# required modules
use warnings;
use strict;
#use diagnostics;

use Getopt::Long;
use Data::Dumper;
use FindBin;

# ADTool modules
use lib "$FindBin::Bin";
use ADTool::DataSrc;
use ADTool::Configs;
use ADTool::ENKLd;
use ADTool::RefSet;
use ADTool::ADTest;

$|++;

# read arguments
my $config_file;
my $log_file;
my $help;

my $alarm = 0; # activate alarm

my $opt = GetOptions(
	"config=s"	=>	\$config_file,
	"alarm"		=> 	\$alarm,
	"log=s"		=>	\$log_file,
	"help"		=>	\$help
);

if(!$opt || $help || !$config_file) {
	print STDERR "Usage: [cmd] --config=adtoolconfig.xml (--log=logfile.txt)\n";
	exit 1;
}

if(!$log_file) {
	$log_file = "/dev/null";
}
open OUTPUT, ">$log_file" or die "Unable to open log file handler: $!";

# log file handler
#if($log_file) {
#	open LOG, ">>$log_file" or die "Unable to open handler to log file: $!";
#	print LOG "\n\n\n";
#	local $Log::Message::Simple::DEBUG_FH   = \*LOG;
#	select(LOG);
#	$|++;
#	select(STDOUT);
#}


my $dtxt = "[---main-loop---]";

debug "########################################################################################",V;
debug "######################################## ADTool ########################################",V;
debug "########################################################################################",V;
debug "",V;
debug "                               *** DEBUGGING ENABLED ***                                ",V;
debug "",V;


if($alarm) {
	debug "$dtxt Darwin alarming enampled",V;
}

# ADTool configuration, get all parameters
my $adconf = ADTool::Configs->new($config_file);
my $t_start = $adconf->getTimeStart;		# analysis start
my $t_end   = $adconf->getTimeEnd;		# analysis end
my $t_gran  = $adconf->getTimeGranularity;	# time granularity (seconds)
my $f_name  = $adconf->getFeatureName;		# traffic feature
my $var_name= $adconf->getVariableName;		# variable (eg. server_ip)
my $refwin_width = $adconf->getRefWindowWidth;	# reference window width (days)
my $refwin_guard = $adconf->getRefWindowGuard;	# guard period (hours)
my $slack  = $adconf->getSlackVariable;		# slack variable
my $min_distr_size = $adconf->getMinDistrSize;  # minimum allowed distribution size
my $min_refset_size= $adconf->getMinRefSetSize;	# minimum allowed refset size
my $m_param = $adconf->getM;			# m parameter (top M distributions from refset)
my $alpha = $adconf->getAlpha;			# alpha paramenter (test sensitivity)
$0 = "adt:$var_name";

######################## TO-DO ###############################
####open DIA, "> deleteme_diagnosis_$var_name-$f_name.txt" or die $!;
##############################################################


# start DBStream connection
my $datasrc = ADTool::DataSrc->new(
	$adconf->getDBhost,$adconf->getDBport,$adconf->getDBname,
	$adconf->getDBuser,$adconf->getDBpass,
	$adconf->getFeaturesTable,$adconf->getFlagsTable,$adconf->getDriftsTable,
	$adconf->getVariableName, $adconf->getFeatureName);

# get start-end of features table from database
my $f_start = $datasrc->getFirstFeaturesTimeBin;
my $f_end   = $datasrc->getLastFeaturesTimeBin;
debug "$dtxt Features table: start=$f_start, end=$f_end",V;

# checking time constraints
my $min_start = $f_start + ($refwin_width*86400);
if( $t_start < $min_start) {
	die 	"[ERROR] Data start at $f_start. Not enough data in features table to start ".
		"analysis at $t_start (min $min_start).\n".
		"        Wait for more data to be available or decrease the ".
		"reference window width and guard\n";
}

# create flags table if it does not exist
$datasrc->createFlagsTable;
$datasrc->createDriftTable;

# get last classified time bin
my $lastClassBin = $datasrc->getLastClassifiedBin();

# execute fake training in reference window if flags table is empty
unless($lastClassBin) {
	my $train_start = $t_start-($refwin_width*86400)-$t_gran;
	my $train_end   = $t_start-$t_gran;
	$datasrc->executeFakeTraining($train_start,$train_end,$t_gran);
}

# define first reference window (to be updated at every iteration)
my $refwin_start = $t_start-($refwin_width*86400)-$t_gran*2;
my $refwin_end   = $t_start-($refwin_guard*3600)-$t_gran*2;
debug "$dtxt First reference window [$refwin_start:$refwin_end]",V;

# define variables for execution loop
my $current   = $t_start;
my $prev_timestamp = $t_start-$t_gran;
my $code = 0;
my $iter_count = 1;

# disconnect from database if receive SIGKILL
$SIG{INT} = sub {
	debug "",V; debug "",V; 
	$datasrc->disconnect;
	die "[NOTIFY] ADTool manually stopped. Last classified timebin=$current\n";
};

sub time_hr {
	my ($time) = @_;
	my ($sec,$min,$hour,$mday,$mon,$year) = localtime($time);
	$mon++;
	$sec = "0$sec" if $sec < 10; $mday = "0$mday" if $mday < 10;
	$min = "0$min" if $min < 10; $mon  = "0$mon"  if $mon  < 10;
	$hour="0$hour" if $hour< 10; $year = $year-=100;
	my $time_hr = "$hour:$min:$sec $mday/$mon/$year";
	return $time_hr;
}

# execution loop
debug "",V;
debug "",V;
debug "$dtxt Starting now execution loop",V;
debug "",V;
debug "",V;
my $stop_condition = ($t_end != 0) ? $current <= $t_end : 1; # offline vs. online

while($stop_condition) {
	
	# readable timestamp
	my $current_hr = time_hr($current);
	
	# notify iteration start
	debug "$dtxt Iteration #$iter_count (slot $current - $current_hr)",V;

	# taking time at the beginning of iteration
	my $iter_time_start = time;
	
	# variables for this iteration
	my ($score,$gamma,$phi_alpha) = (0,0,0);
	my $drifts = {};

	my $refwin_incr = 0;
	my $refwin_warning = 0;

	# check if data available
	if($datasrc->check_availability($current) > 0) {
	
		# ok, data available. Go on
		debug "$dtxt Data available for this iteration. Go on with the test...",V;
		
		# check code for previous execution
		my $prev_code = $datasrc->get_flag($prev_timestamp);
		
		# ################## REFERENCE WINDONW MNGMNT ################ #
		
		my $refwin_incr = 0;
		#my $refwin_warning = 0;
		
		# shift window start if previous timebin was normal or
		# window is currently too large (shift of two slots if both)
		if($prev_code == 0) {
			$refwin_incr += $t_gran;
			if(($refwin_end-$refwin_start)>($refwin_width*86400)) {
				$refwin_incr += $t_gran;
			} 
		}
		elsif (($refwin_end-$refwin_start)>(1.5*$refwin_width*86400)) {
			$refwin_warning = 1;
		}
		
		if(($refwin_end-$refwin_start)>=(2*$refwin_width*86400)) {
			$refwin_incr += $t_gran;
		}
		
		
		# hook window end to current timebin
		$refwin_end   = $current - ($refwin_guard*3600); 
		$refwin_start += $refwin_incr;
		
		debug "$dtxt Update reference window [$refwin_start:$refwin_end]",V;
		debug "$dtxt Reference window size: ".(($refwin_end-$refwin_start)/3600)." hours",V;
		
		# ############################################################ #
				
		# compute reference set
		my $refset = ADTool::RefSet->new($datasrc,$current,
						$refwin_start,$refwin_end,
						$min_distr_size,$min_refset_size,
						$slack,$refwin_warning);
		my $refset_code = $refset->getCode;
		my $refset_size = $refset->getRawSize;	
		
				
		# if reference set was ok, then continue with analysis
		if ($refset_code == 0 || $refset_code == 3) {
			debug "$dtxt Reference set ready. Now running analysis...",V;
			
			$gamma          = $refset->getGamma($m_param);
			my $currentPDF  = $refset->getCurrentPDF();
			my $closestPDFs = $refset->getTopPDFs($m_param);
			#my $allPDFs     = $refset->getAllPDFs();
			
			my $adtest = ADTool::ADTest->new($currentPDF,$closestPDFs,
							$gamma,$alpha);
			my $test_code = $adtest->getCode;
		
			# retrieve output code, score, etc.
			$score = $adtest->getScore;
			#$gamma = $adtest->getGamma;
			$phi_alpha = $adtest->getPhiAlpha;
		
			#####$code = $test_code; # can be either 0 or 1
			
			## DIAGNOSIS
			if ($test_code == 1 || $refset_code == 3) {
				$drifts = $adtest->driftvars($adconf->getDriftPercentile);
				$datasrc->update_drift($current,$drifts);
				
			}
			
			if($refset_code == 3) { $code = $refset_code }
			else { $code = $test_code }
		}
		else {
			$code = $refset_code; # can be either 2 or 3
		}
		
	}
	
	
	else {
		# data is not available, hole or wait for new data?
		
		# check if hole in data or just waiting
		my $last_feat_ts = $datasrc->getLastFeaturesTimeBin; # can't use old anymore
		if ($last_feat_ts > $current) {
			debug "$dtxt This timeslot is missing. No data, code 4",V;
			$code = 4; # missing data
		}
		
		# it seems that we just need to wait a bit more (sleep)
		else {
			#my $now  = time;
			#my $sleep_dur = ($t_gran - ($now % $t_gran) +1)/2;
			#debug "$dtxt Waiting data for slot $current... (sleep=$sleep_dur)",V;
			#sleep($sleep_dur);
			debug "$dtxt Waiting data for slot $current... ".
			      "(sleep for $t_gran sec)",V;
			my $sleep_timer = $t_gran/2;
			sleep($sleep_timer);
			next; # sleep and try again
		}
	}	


	if($code == 0 && $refwin_warning == 1) {
		debug "$dtxt [WARNING!] Possible change of working point",V;
	}

	# check if this time slot has been classified previously
	my $old_code = $datasrc->check_if_classified($current);

	# log result of file
	$phi_alpha = 0 unless defined $phi_alpha;
	print OUTPUT "$current\t$code\t$score\t$gamma\t$phi_alpha\n";

	# log result on database
	if($old_code == -1) {
		debug "$dtxt This time bin was not previously present in flags table",V;
		$datasrc->insert_flag($current,$code,$score,$gamma,$phi_alpha);
	}
	elsif($old_code != $code) {
		debug "$dtxt Warning: this time slot was previously code=$old_code. Updating to code=$code",V;
		$datasrc->update_flag($current,$code,$score,$gamma,$phi_alpha);
	}
	else {
		debug "$dtxt This time bin was already classified with same code. Update gamma,phi_alpha",V;
		$datasrc->update_flag($current,$code,$score,$gamma,$phi_alpha);
	}	
	
	# taking time at the end of the iteration
	my $iter_time_end = time;
	my $iter_duration = $iter_time_end - $iter_time_start;

	# iteration complete
	debug "$dtxt Iteration #$iter_count completed in $iter_duration seconds. Result code=$code score=$score",V;
	if($iter_duration > $t_gran) {
		debug "$dtxt WARNING!!!!! This iteration took longer than $t_gran seconds (time gran.)!!",V;
	}
	debug "",V;
	debug "",V;
	

	# update current timestamp variable
	$prev_timestamp=$current;
	$current+=$t_gran;
	$iter_count++;
	
	# decide if continue or exit execution loop
	$stop_condition = ($t_end != 0) ? $current <= $t_end : 1; # offline vs. online
}

# outside the loop
debug "",V; debug "",V;
debug "$dtxt Reached end of the analysis (it was off-line). Bye bye",V;

# disconnect from database and exit
$datasrc->disconnect;
exit 0;
