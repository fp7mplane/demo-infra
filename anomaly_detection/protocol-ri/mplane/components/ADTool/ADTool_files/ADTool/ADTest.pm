package ADTool::ADTest;

# This module implement the test part of the AD algorithm
# It generate an output code (0 if normal, 1 if anomalous) comparing
# a PDF distributions of values with a reference set
#
# Pierdomenico Fiadino - fiadino@ftw.at
# Vienna, 01/04/2014 version 1 
# Vienna, 05/12/2014 version 2 (added diagnosis part)

use strict;

# debugging
use Data::Dumper;
use Log::Message::Simple qw /debug/;
use constant V  => 1; # verbouse
use constant VV => 0; # very verbous
my $dtxt = "[ADTool::ADTest ]";

sub new {
	my ($class,$currentPDF,$refset,$gamma,$alpha) = @_;
	my $self  = {
		_current_pdf => $currentPDF,
		_refset	=> $refset,
		_alpha => $alpha,
		_gamma => $gamma
	};
	bless $self, $class;
	$self->execute;
	return $self;
}

sub execute {
	my ($self) = @_;
	my $currentPDF = $self->{_current_pdf};
	my $refsethash = $self->{_refset};
	my $alpha = $self->{_alpha};
	my $enkl = new ADTool::ENKLd;

	
	# compute m(m-1)/2 distances (among distributions in refset)
	debug "$dtxt Now computing m*(m-1)/2 divergences in RefSet",V;
	my $dist_hash = {}; my @dist_array;
	foreach my $i (keys %$refsethash) {
		foreach my $j (keys %$refsethash) {
			unless(exists $dist_hash->{$i}->{$j} or $i==$j) {
				my $i_val = ADTool::RefSet->extractValues($refsethash->{$i});
				my $j_val = ADTool::RefSet->extractValues($refsethash->{$j});
				my $dist  = $enkl->divergence($i_val,$j_val);
				$dist_hash->{$i}->{$j} = 1; # avoid computing same distance
				$dist_hash->{$j}->{$i} = 1; # avoid computing same distance
				push @dist_array,$dist;
			}
		}
	}
	
	# phi_alpha
	@dist_array = sort {$a <=> $b} @dist_array;
	my $alpha_perc = int((scalar(@dist_array))*(1-$alpha)+0.5)-1;
	my $phi_alpha  = $dist_array[$alpha_perc];
	$self->{_phialpha} = $phi_alpha;
	debug "$dtxt Phi_alpha(t) = $phi_alpha",V;
	
	$phi_alpha = 0 unless($phi_alpha);
	
	# compute avg of m distances (among current distribution and distrib. in refset)
	#debug "$dtxt Now computing m divergences between current PDF and RefSet",V;
	#my ($dist_sum,$dist_cnt) = (0,0);
	#my $current_val = ADTool::RefSet->extractValues($currentPDF);
	#foreach my $pdf (keys %$refsethash) {
	#	my $pdf_val = ADTool::RefSet->extractValues($refsethash->{$pdf});
	#	my $dist = $enkl->divergence($current_val,$pdf_val);
	#	$dist_sum+=$dist;
	#	$dist_cnt++;
	#}
	
	# gamma
	#my $gamma = ($dist_cnt != 0)? ($dist_sum / $dist_cnt) : 0;
	#$self->{_gamma} = $gamma;
	my $gamma = $self->{_gamma};
	debug "$dtxt Gamma(t) = $gamma",V;
	
	my $code;
	if ($gamma>$phi_alpha) {
		$code = 1;
		$self->{_score} = ($gamma-$phi_alpha)/$phi_alpha;
		debug "$dtxt Anomalous timebin with score = $self->{_score}",V
	}
	else {
		$code = 0;
		debug "$dtxt All ok, output code = 0",V;
	}
	
	# save code
	$self->{_code} = $code;
}

sub getCode {
	return shift->{_code};
}

sub getGamma {
	return shift->{_gamma};
}

sub getPhiAlpha {
	return shift->{_phialpha};
}

sub getScore {
	my ($self) = @_;
	if ($self->{_code} != 1) { return 0; }
	return $self->{_score};
}

# compute average counters for all variables in reference set
sub averages {
	my ($self) = @_;
	my $refsethash =  $self->{_refset};
	my $sum = {};
	my $cnt = {};
	my $avg = {};

	foreach my $timebin (keys %$refsethash) {
		my $this_pdf = $refsethash->{$timebin};
		foreach my $var (keys %$this_pdf) {
			$sum->{$var} += $this_pdf->{$var}->{'feature'};
			$cnt->{$var} ++;
		}
	}
	foreach my $var (keys %$sum) {
		$avg->{$var}->{'feature'} = $sum->{$var} / $cnt->{$var};
	}
	return $avg;
}

# reference set variance for each variable [DEPRECATED]
sub std_dev {
	my ($self) = @_;
	my $refsethash =  $self->{_refset};
	my $sum = {};
	my $cnt = {};
	my $avg = $self->averages;
	my $variance = {};

	foreach my $timebin (keys %$refsethash) {
		my $this_pdf = $refsethash->{$timebin};
		foreach my $var (keys %$this_pdf) {
			$sum->{$var} += ($this_pdf->{$var}->{'feature'} - 
				$avg->{$var}->{'feature'})**2;
			$cnt->{$var} ++;
		}
	}
	foreach my $var (keys %$sum) {
		$variance->{$var}->{'feature'} = sqrt($sum->{$var} / $cnt->{$var});
	}
	return $variance;
}


# compare the counters of current distribution with the averages from the
# reference set, then return the variables that present the largest variation
sub driftvars {
	my ($self,$perc) = @_;

	$perc = 0.25 unless $perc;

	debug "$dtxt Computation of top drift vars started with perc=$perc...",V;

	my $currentPDF = $self->{_current_pdf}; # current distribution
	my $averages   = $self->averages();	# average distribution (ref.set)
	
	#my $std_devs   = $self->std_dev();	# standard deviations
	
	my $n = scalar(keys %$averages); 	# number of variables

	debug "$dtxt Total variables: $n found",VV;

	my $t_ref; 					# sum of average counters
	map {$t_ref += $_} (map {$averages->{$_}->{'feature'}} keys %$averages);
	
	debug "$dtxt Sum of average counters: $t_ref",VV;
	
	# sum of counters in current PDF
	my $t_cur; map {$t_cur += $_} (
		map {$currentPDF->{$_}->{'feature'}} 
		keys %$currentPDF
	);
		
	debug "$dtxt Sum of counters in current PDF: $t_cur",VV;
		
	my $drifts;				# this will contain drifts
	my $drift_sum = 0;			# sum of drift values

	foreach my $var (sort keys %$currentPDF) {

		
		my $current = $currentPDF->{$var}->{'feature'};
		   $current = 1e-20 if $current == 0;
		
		my $average = $averages->{$var}->{'feature'};
		   $average = 1e-20 if $average == 0;

		#my $std_dev = $std_devs->{$var}->{'feature'};
		#my $min = $average - ($k * $std_dev);
		#my $max = $average + ($k * $std_dev);
		
		my $drift = ($current * (log($current/$average)/log(2)));
		
		debug "$dtxt var=$var\tcurr=$current\tavg=$average\tdrift=$drift abs(drift)=".abs($drift),VV if ($drift!=0);
		
		#if   ($current > $max)	{ $drift = ($current-$max)/$t_cur; }
		#elsif($current < $min)	{ $drift = ($current-$min)/$t_cur; }
		#else			{ 				   }

		#$drift = sprintf "%.18f",$drift;
		
		$drift_sum+=abs($drift);
		
		$drifts->{$var}->{'drift'} = $drift;
		$drifts->{$var}->{'current'} = $current;
		$drifts->{$var}->{'average'} = $average;
	}
	
	my $drift_incr = 0;
	my $drift_perc = $drift_sum * $perc;
	
	debug "$dtxt Drift sum: $drift_sum. Drift $perc%: $drift_perc",VV;
	
	my @drifting_vars =	sort {
					#my $x = ($drifts->{$a}<0)? -1*$a : $a;
					#my $y = ($drifts->{$b}<0)? -1*$b : $b;
					#$y cmp $x;
					abs($drifts->{$b}->{'drift'}) <=> abs($drifts->{$a}->{'drift'})
				} 
				keys %$drifts;

 	debug "$dtxt Top drifting variables (perc=$perc):",V;
 	
 	my $drifts_perc;
 	for(my $i = 0; $i < scalar(@drifting_vars) && $drift_incr < $drift_perc; $i++) {
 		$drifts_perc->{$drifting_vars[$i]} = $drifts->{$drifting_vars[$i]};
 		$drift_incr += abs($drifts->{$drifting_vars[$i]}->{'drift'});
 		debug "$dtxt ".($i+1)."\t [$drifts->{$drifting_vars[$i]}->{'drift'}]\t$drifting_vars[$i]\t$drift_incr",V;
 	}
	
	return $drifts_perc;
}

1;
