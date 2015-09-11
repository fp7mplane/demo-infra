package ADTool::RefSet;

# Reference set object
#
# Pierdomenico Fiadino (fiadino@ftw.at)
# Vienna, 26/02/2014 - version 1
# Vienna, 12/12/2014 - version 1.1 bugfixing

use strict;

# debugging
use Data::Dumper;
use Log::Message::Simple qw /debug/;
use constant V  => 1; # verbouse
use constant VV => 0; # very verbous
our $dtxt = "[ADTool::RefSet ]";

# constructor
sub new {
	my ($class,$dbobj,$current,$start,$end,$mindistr,$minrefset,$slack,$warn) = @_;

	my $self = {		
		_datasrc	=> $dbobj,	# datasrc handler
		_current	=> $current,	# current time bin
		_refwin_start	=> $start,	# beginning of reference window
		_refwin_end	=> $end,	# end of reference window
		_min_distr_size	=> $mindistr,	# minimum distribution size
		_min_refset_size=> $minrefset,	# minimum refset size
		_slack		=> $slack,	# slack var for size comparison
		_warning	=> $warn	# warning mode (long lasting an.)
	};

	debug "$dtxt Create RefSet object for timebin $current in [$start:$end]",V;	
	bless $self, $class;
	
	# compute reference set
	$self->compute;
	
	return $self;
}

# hidden method that contain the extraction of refset logic
sub compute {
	my ($self) = @_;
	my $datasrc		= $self->{_datasrc};
	my $current		= $self->{_current};
	my $refwin_start	= $self->{_refwin_start};
	my $refwin_end		= $self->{_refwin_end};
	my $min_distr_size	= $self->{_min_distr_size};
	my $min_refset_size	= $self->{_min_refset_size};
	my $slack		= $self->{_slack};

	# refset code (0 if ok, 2 or 3 if problems)
	my $code = undef;	
	
	# get current distribution
	my $current_pdf = $datasrc->getPDF($current);
	$self->{_current_pdf} = $current_pdf;
	
	# first check: current distribution has enough samples (code 2)
	
	#my $current_size = scalar(keys %$current_pdf); # this is when i was using count of variables for comp.
	my $current_size = $datasrc->getPDFSize($current); # now i am comparing the sum of counters
	
	if ($current_size < $min_distr_size) {
		# first check not passed, terminate iteration with code 2
		debug "$dtxt Current distribution has not enough samples ($current_size)",V;
		$code = 2; 
	}
	else {
		# first check passed, go ahead
		debug "$dtxt OK, current distribution has enough samples ($current_size)",V;
	
		# second check: refset contains enough distributions with proper size
		
		#  this commented code is for the fixed slack factor (older version)
		#my ($min_size,$max_size) = ($current_size*(1-$slack),$current_size*(1+$slack));
		#my $refset = $datasrc->getRefSet($refwin_start,$refwin_end,$min_size,$max_size,$self->{_warning});
		#my $refsetsize = scalar(keys %$refset);
		
		# this loop is the new version with incremental slack factor
		my ($min_size,$max_size);
		my $refset; my $refsetsize;
		my $s;
		for($s = 0; $s <= $slack; $s+=0.01) {
			($min_size,$max_size) = ($current_size*(1-$s),$current_size*(1+$s));
			$refset = $datasrc->getRefSet($refwin_start,$refwin_end,$min_size,$max_size,$self->{_warning});
			$refsetsize = scalar(keys %$refset);
			if($refsetsize >= $min_refset_size) {
				last; # no need to increase $slack any more, this is enough
			}
		}
		
		# if still didn't reach the required size... give up
		if($refsetsize < $min_refset_size) {
			# second check not passed, terminate iteration with code 3
			debug "$dtxt Reference set size too small ($refsetsize)",V;
			$code = 3;
		}
		else {
			# second check passed, go ahead
			debug "$dtxt OK, reference set has enough distributions ($refsetsize) with s=$s",V;
			
			# save raw refset for later
			$self->{_rawrefset} = $refset;
			
			# compute distances
			$self->computeDistances;
			
			# all ok
			$code = 0;
		}
	}
	
	# save code for later
	$self->{_code} = $code;
	
	#debug "$dtxt RefSet filtering finished (RefSet code=$code)",V;
	#return $code;
}


# takes as input a PDF distribution and a domain (list of variables with values
# always 0) and return an "inflated" PDF containing all the variables in the domain
sub augmentPDF {
	my ($self,$pdf,$domain) = @_;
	my $augmented = {};
	foreach my $var (keys %$domain) {
		my $val = (exists $pdf->{$var}) ? 
				$pdf->{$var}->{'feature'} : 0;
		$augmented->{$var}->{'feature'} = $val;
	}
	return $augmented;
}

# extract the values of a PDF distribution in form of a sorted array reference
# (the variable names are cut away)
sub extractValues {
	my ($self,$pdf) = @_;
	my $array_ref = [];
	foreach my $var (sort keys %$pdf) {
		push @$array_ref,$pdf->{$var}->{'feature'};
	}
	return $array_ref;
}

# EXTERNAL DISTANCES
# compute distances between current distributions and all distributions in refset
sub computeDistances {
	my ($self) = @_;
	
	# database handler
	my $datasrc = $self->{_datasrc};
	
	# ENKL object
	my $enkl = new ADTool::ENKLd;
	
	# define domain window, retrieve domain set from db and save it
	my $rw_start = $self->{_refwin_start};			# domain start
	my $rw_end   = $self->{_refwin_end};			# domain end
	my $curr    = $self->{_current};		
		
	my $domain  = $datasrc->getDomain($rw_start,$rw_end,$curr);# domain hashref
	#$self->{_domain} = $domain;				# save domain
	
	# retrieve current PDF and 'inflate' it using domain
	my $current_pdf	    = $self->{_current_pdf};
	my $current_pdf_aug = $self->augmentPDF($current_pdf,$domain);
	my $current_values  = $self->extractValues($current_pdf_aug);
	$self->{_current_pdf_aug} = $current_pdf_aug;
	
	# scan all PDFs in refset, 'inflate' them and compute distance with current
	debug "$dtxt Computing distances between current distrib. and reference set",V;
	my $rawrefset = $self->{_rawrefset};
	my $augrefset = {};
	my $divergences = {};
	my ($div_cnt,$div_sum) = (0,0);
	foreach my $tbin (keys %$rawrefset) {
		# retrieve PDF corresponding to $tbin
		my $this_pdf     = $rawrefset->{$tbin};
		
		# inflate PDF using all variables in domain and save inflated version
		my $this_pdf_aug = $self->augmentPDF($this_pdf,$domain);
		$augrefset->{$tbin} = $this_pdf_aug;
		
		# extract sorted list of values from augmented PDF (not variables!)
		my $this_values  = $self->extractValues($this_pdf_aug);
		
		# compute distance with current distribution and save it
		my $this_div     = $enkl->divergence($current_values,$this_values);
		$divergences->{$tbin} = $this_div;
		
		# update counters for computing gamma
		$div_sum += $this_div;
		$div_cnt ++;
	}
	
	# comput gamma and save it
	$self->{_gamma} = ($div_cnt>0)? ($div_sum/$div_cnt) : 0;
	
	# save divergences and inflated versions of PDFs for later
	$self->{_divs} = $divergences;
	$self->{_augrefset} = $augrefset;
}

# return distribution corresponding to current time bin
sub getCurrentPDF {
	return shift->{_current_pdf_aug};
	
}

# return size of the raw reference set
sub getRawSize {
	my ($self) = shift;
	my $rawset_ref = $self->{_rawrefset};
	return scalar(keys %$rawset_ref);
}

# return arrayref of topM distributions in reference set
sub getTopPDFs {
	my ($self,$mvar) = @_;
	
	# it contains all distances (computed before)
	my $divs = $self->{_divs}; 
	
	# array of topM closest PDFs in refset
	my @tops = (sort {$divs->{$a} <=> $divs->{$b}} keys %$divs)[0..$mvar-1]; 
	
	# rebuild "reduced" reference set containing topM distributions only
	my $top_refset = {};
	foreach my $tbin (@tops) {
		
		$top_refset->{$tbin} = $self->{_augrefset}->{$tbin};
	}
	
	# return reduced refset
	return $top_refset;
}

# return gamma value as avg divergence with TopM distributions
sub getGamma {
	my ($self,$mvar) = @_;
	
	# it contains all distances (computed before)
	my $divs = $self->{_divs}; 
	
	# array of topM closest PDFs in refset
	my @tops = (sort {$divs->{$a} <=> $divs->{$b}} keys %$divs)[0..$mvar-1]; 
	
	
	### MAYBE A PROBLEM IF IT IS RUNNING AT ERRORCODE 3 for GETTING DRIFT VARS
	if(scalar(@tops) < $mvar) {
	##	print STDERR "[ERROR] $dtxt Not enough distributions in RefSet. How did you get here btw?\n";
		debug "$dtxt [WARNING] m=$mvar is greater than #"."tops=".scalar(@tops),V;
	##	exit 0;
	}
	
	# rebuild "reduced" reference set containing topM distributions only
	my ($div_sum,$div_cnt) = (0,0);
	foreach my $tbin (@tops) {
		my $div = $divs->{$tbin};
		$div_sum +=$div;
		$div_cnt ++;
		
	}
	my $gamma = ($div_cnt!=0)? $div_sum/$div_cnt : 0;
	return $gamma;
}

# return arrayref of all distributions in reference set
sub getAllPDFs {
	return shift->{_augrefset};
}

# return refset code (0 if refset is ok, 2 or 3 otherwise)
sub getCode {
	return shift->{_code};
}

1;
