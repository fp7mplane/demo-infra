package ADTool::Configs;

# This module provides the configuration parameters for ADTool.
# The settings are parsed from an XML file using the XML::Simple module.
# See the constructor for the list of required arguments.
#
# Pierdomenico Fiadino (fiadino@ftw.at)
# Vienna 21/02/2014 - version 1
# Vienna 03/02/2015 - version 1.1

# modules
use strict;
use XML::Simple; # debian package 'libxml-simple-perl'

# debugging
use Log::Message::Simple qw /debug/;
use constant V => 1; # activate debugging
my $dtxt = "[ADTool::Configs] ";


# constructor
sub new {
	my $class = shift;
	my $file  = shift;

	my $xs = XML::Simple->new or die "[ERROR] Unable to open XML config file";
	my $config = $xs->XMLin($file) or die "[ERROR] Unable to parse XML config file";
	
	my $self = {};

	$self->{_file}  = $file;										# config XML file name

	$self->{_addr}  = $config->{Database}->{host};			# database hostname
	$self->{_port}  = $config->{Database}->{port};			# database port
	$self->{_dbname}= $config->{Database}->{dbname};		# database name
	$self->{_user}  = $config->{Database}->{user};			# database username
	$self->{_passw} = $config->{Database}->{password};		# database password
	
	$self->{_features}  = $config->{Database}->{features_table};	# features table
	$self->{_flags}     = $config->{Database}->{flags_table};	# flags table
	$self->{_drifts}     = $config->{Database}->{drifts_table};	# flags table

	$self->{_tstart} = $config->{Analysis}->{start};		# start timestemp for analysis
	$self->{_tend}   = $config->{Analysis}->{end};			# end timestamp for analysis (0 means run online)
	$self->{_granularity} = $config->{Analysis}->{granularity};	# time granularity
	$self->{_fname}  = $config->{Analysis}->{feature};				# traffic feature name
	$self->{_varname}= $config->{Analysis}->{variable};				# variable of the distributions
	$self->{_drvarperc} = $config->{Analysis}->{drift_percentile};	# percentile of drifting variables to be saved


	$self->{_refsetwidth} = $config->{RefSet}->{width};				# reference window width
	$self->{_refsetguard} = $config->{RefSet}->{guard};				# reference window guard time

	$self->{_mindistrsize}  = $config->{RefSet}->{min_distr_size};	# min allowed size for current distribution
	$self->{_minrefsetsize} = $config->{RefSet}->{min_refset_size};	# min allowed size of reference set
	$self->{_slackvar}      = $config->{RefSet}->{slack_var};		# slack variable for comparing distr sizes
	$self->{_mvar}				= $config->{RefSet}->{m};				# number of distributions to consider in refset
	$self->{_kvar}				= $config->{RefSet}->{k};				# number of clusters for pruning

	$self->{_alpha}	= $config->{ADTest}->{alpha};					# sensitivity
	
	$self->{_descr} = $config->{Description};			# task description

	if ($self->{_mvar} > $self->{_minrefsetsize}) {
		debug "[WARNING] $dtxt m_par > min_refset_size. I will shrink it...\n";
		$self->{_mvar} = $self->{_minrefsetsize};
	}

	bless $self, $class;
	$self->check_args;

	# debugging
	debug "",V;
	debug "$dtxt Configuration parser instanciated",V;
	debug "$dtxt Summary of settings: ",V;
	debug "$dtxt Database $self->{_dbname}\@$self->{_addr}",V;
	debug "$dtxt Features table: $self->{_features}",V;
	debug "$dtxt Flags table:    $self->{_flags}",V;
	debug "$dtxt Time granularity $self->{_granularity} (start=".$self->{_tstart}.",end=".$self->{_tend}.")",V;
	debug "",V;

	return $self;
}

# check if all arguments are present in the XML file
sub check_args {
	my ($self) = @_;
	foreach my $arg (keys %$self) {
		die "[ERROR] Missing argument $arg" unless( exists $self->{$arg});
	}
}

# getters
sub getDBuser 			{ return shift->{_user};		}
sub getDBpass 			{ return shift->{_passw};		}
sub getDBname 			{ return shift->{_dbname};		}
sub getDBhost 			{ return shift->{_addr};  		}
sub getDBport 			{ return shift->{_port};  		}

sub getFeaturesTable 	{ return shift->{_features}; 	}
sub getFlagsTable   	{ return shift->{_flags};    	}
sub getDriftsTable   	{ return shift->{_drifts};    	}

sub getTimeStart		{ return shift->{_tstart}; 		}
sub getTimeEnd			{ return shift->{_tend};   		}
sub getTimeGranularity	{ return shift->{_granularity};	}
sub getFeatureName		{ return shift->{_fname};  		}
sub getVariableName		{ return shift->{_varname};		}
sub getDriftPercentile	{ return shift->{_drvarperc};	}

sub getRefWindowWidth	{ return shift->{_refsetwidth}; }
sub getRefWindowGuard	{ return shift->{_refsetguard}; }

sub getMinDistrSize		{ return shift->{_mindistrsize};}
sub getMinRefSetSize	{ return shift->{_minrefsetsize}}
sub getSlackVariable	{ return shift->{_slackvar};	}
sub getM				{ return shift->{_mvar};			}
sub getK				{ return shift->{_kvar};			}

sub getAlpha			{ return shift->{_alpha};		}


sub getDescription	{ return shift->{_descr}; }

1;
