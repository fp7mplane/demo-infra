package ADTool::ENKLd;

# This module provides the computation of the normalized
# Kullback-Leibler divergence between two distribution of values.
# The two distributions are passed to this module as array
# references and do not need to be sorted and normalized.
#
# Pierdomenico Fiadino - fiadino@ftw.at
# Vienna, 20/02/2014 - version 1.0

# used for calculating the sum of values in vectors
use List::Util qw( sum );
use Data::Dumper;

# tiny float to fill 0s in the vectors
use constant TINY => 1e-20;

# debug
use Log::Message::Simple qw /debug/;
use constant V  => 1; # verbouse
use constant VV => 0; # very verbous
our $dtxt = "[ADTool::ENKLd  ]";

# dumb constructor
sub new {
	my $class = shift;
	my $self  = {};
	bless $self, $class;
	debug "$dtxt ENKLd object created",V;
	return $self;
}

# ENKLd main subroutine
sub divergence {
	my ($self, $P, $Q) = @_;
		
	my $P_norm = normalize($P); 
	   $P_norm = fill_zeros($P_norm);
	   $P_norm = normalize($P_norm); # it may be required...

	my $Q_norm = normalize($Q); 
	   $Q_norm = fill_zeros($Q_norm);
	   $Q_norm = normalize($Q_norm); # it may be required...
	   
	#print Dumper($Q_norm,$P_norm)."\n"; 
	  
	my $Hp = entropy($P_norm);
	my $Hq = entropy($Q_norm);
	
	my $ENKL1 = kl($P_norm,$Q_norm) / $Hp;
	my $ENKL2 = kl($Q_norm,$P_norm) / $Hp;
	
	my $ENKL  = ($ENKL1 + $ENKL2) / 2;
	return $ENKL;
}

# kullback–leibler divergence
sub kl {
	my ($P, $Q) = @_;
	
	my $kl = 0;
	for(my $i = 0; $i < scalar(@$P); $i++) {
		#print "ERROR!! ".$Q->[$i]."\n" if ($Q->[$i] == undef);
		$kl += ( $P->[$i] * log2($P->[$i] / $Q->[$i]) );
	}
	
	return $kl;
}

# logarithm base 2
sub log2 {
	my $n = shift;
	return ($n==0)? 0 : log($n)/log(2);
}

# comput entropy of a vector
sub entropy {
	my ($P) = @_;
	
	my $h = 0;
	for(my $i = 0; $i < scalar(@$P); $i++) {
		$h -= ( $P->[$i] * log2($P->[$i]) );
	}
	
	return $h;
}

# normalize a vector
sub normalize {
	my ($P) = @_;
	my $P_size = scalar(@$P);
	my $P_sum  = sum(@$P);
	#my $P_norm = [];
	for(0..$P_size-1) {
		$P->[$_] = $P->[$_]/$P_sum;
	}
	#foreach my $sample (sort {$a<=>$b} @$P) {
	#	push @$P_norm, $sample/$P_size;
	#}
	return $P;
}

# insert a 'TINY float' in array positions containing 0s
sub fill_zeros {
	my ($P) = @_;
	my $P_size = scalar(@$P);
	
	for(0..$P_size-1) {
		$P->[$_] = TINY if ($P->[$_] == 0);
	}
	return $P;
}

1;
