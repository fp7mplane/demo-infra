package ADTool::DataSrc;

# This module provides an interface to the PostgreSQL database
# used by DBStream.
# It allows to connect to the DB, query for the last classified
# time-bin, build the reference set for a specific feature.
#
# Pierdomenico Fiadino - fiadino@ftw.at
# Vienna, 25/02/2014 version 1
# Vienna, 03/04/2014 version 2 (changed format of feature tables, added score to flags)

# modules
use DBI;
use strict;


# debugging (set constant V and VV to 0 to disable)
use Data::Dumper;
use Log::Message::Simple qw /debug/;
use constant V  => 1; # verbouse
use constant VV => 0; # very verbous
our $dtxt = "[ADTool::DataSrc]";


# constructor (initialize database connection) and keep
# database variables
sub new {
	my ($class,$addr,$port,$dbname,$user,$passw,$feat,$flags,$drifts,$var,$f_name) = @_;

	my $dbi = "dbi:Pg:dbname=$dbname;host=$addr;port=$port;";
	my $dbh = DBI->connect($dbi,$user,$passw)
		or die "Can't Connect to database: $DBI::errstr\n";

	debug "",V;
	debug "$dtxt Database interface module instanciated",V;
	debug "$dtxt Successfully connected to database '$dbname'\@$addr:$port",V;
	debug "",V;

	my $self = {
		_var	=> $var,	# variable name (eg. IP)
		_fname	=> $f_name,	# feature name (eg. vol_down)
		_addr	=> $addr,	# database addreass
		_port	=> $port,	# database port
		_dbname => $dbname,	# database name
		_user	=> $user,	# database user-name
		_passw	=> $passw,	# database password
		_feat	=> $feat,	# features table
		_flags  => $flags,	# flags table
		_drifts => $drifts,	# drifts table
		_dbh	=> $dbh		# database handler
	};
	
	bless $self, $class;
	return $self;
}

# instert result code (flag) for a specified time-bin 
# and for a specific feature
sub insert_flag {
	my ($self,$timestamp,$outcome,$score,$gamma,$phi_alpha) = @_;
	my $target = $self->{_flags};
	my $dbh = $self->{_dbh};
	my $feature = $self->{_fname};
	
	$gamma = 0 unless defined $gamma;
	$phi_alpha = 0 unless defined $phi_alpha;
	
	my $sql = "INSERT INTO $target VALUES ($timestamp,'$feature',$outcome,$score,$gamma,$phi_alpha)";
	
	my $sth = $dbh->prepare($sql);
	   $sth->execute;

	debug "$dtxt DB insert: time slot \@$timestamp, feature '$feature', code $outcome",VV;
	return;
}

# update an existing result code (flag) for a specified time-bin
# and feature
sub update_flag {
	my ($self,$timestamp,$outcome,$score,$gamma,$phi_alpha) = @_;
	my $target = $self->{_flags};
	my $dbh    = $self->{_dbh};
	my $feature = $self->{_fname};
	$phi_alpha = 0 unless defined $phi_alpha;
	my $sql    = "UPDATE $target SET code=$outcome, score=$score, gamma=$gamma, phi_alpha = $phi_alpha WHERE serial_time=$timestamp AND feature_name='$feature'";

	my $sth = $dbh->prepare($sql);
	   $sth->execute;
	
	debug "$dtxt Update: time slot \@$timestamp, feature '$feature', code 'outcome",VV;
	return;
}

# ret
sub get_flag {
	my ($self,$timestamp) = @_;
	my $flags_tab = $self->{_flags};
	my $dbh = $self->{_dbh};
	my $fname = $self->{_fname};
	my $sql = "SELECT code FROM $flags_tab WHERE serial_time = $timestamp AND feature_name = '$fname'";
	
	my $res = $dbh->selectrow_arrayref($sql);

	my $code= ($res)? $res->[0] : -1;

	debug "$dtxt Flag \@$timestamp for feature '$fname' = $code",V;

	return $code;
	   
}

# given a variable and a feature, retrieve corresponding
# PDF at the specified timestamp
sub getPDF {
	my ($self,$timestamp,$var) = @_;
	my $dbh      = $self->{_dbh};
	my $feat_tab = $self->{_feat};
	my $variable      = $self->{_var};
	my $feature  = $self->{_fname};
	
	my $query =	"SELECT serial_time, $variable as variable, feature_value AS feature ".
			"FROM $feat_tab ".
			"WHERE serial_time = $timestamp AND feature_name = '$feature' ".
			"ORDER BY 1,2 ASC";

	my $pdf = $dbh->selectall_hashref($query,2) 
		or die "DBI: unable to retrieve PDF\@$timestamp\n";
	
	#my $res	= { $timestamp => $pdf };
	my $res = $pdf;	
	#print Dumper($res);
	
	debug "$dtxt Retrieving PDF \@$timestamp ".
		  "for feature $feature",V;
	debug "$dtxt Query: $query",VV;
	debug "$dtxt PDF retrieved, size ".scalar(keys %$pdf),V; # error here

	return $res;
}

# return the 'size' of a PDF at a given time bin. size=sum(feature_value)
sub getPDFSize {
	my ($self,$timestamp,$var) = @_;
	my $dbh      = $self->{_dbh};
	my $feat_tab = $self->{_feat};
	my $variable      = $self->{_var};
	my $feature  = $self->{_fname};
	
	my $query = 	"SELECT sum(feature_value) as sum
			FROM $feat_tab 
			WHERE serial_time = $timestamp and feature_name = '$feature'";
			
			
	my $size = $dbh->selectrow_arrayref($query);
	my $size_num = $size->[0];
	if(undef $size or $size_num == 0) {
		die "Error: Tab $feat_tab at $timestamp: sum(feature_value)=0\n";
	}
	return $size_num;

}


# return the domain of a specific time window
# (eg. all seen server IPs)
sub getDomain {
	my ($self,$start,$end,$curr) = @_;
	my $dbh       = $self->{_dbh};
	my $feat_tab  = $self->{_feat};
	my $feature = $self->{_fname};
	my $variable = $self->{_var};
	my $query = "with foo as (".
        	    "	SELECT $variable as variable, 0 AS feature ".
		    "	FROM $feat_tab ".
		    "	WHERE serial_time BETWEEN $start AND $end AND feature_name = '$feature' ".
		    "	GROUP BY 1 ".
		    "	UNION ALL ".
		    "	SELECT $variable as variable, 0 AS feature ".
		    "	FROM $feat_tab ".
		    "	WHERE serial_time = $curr AND feature_name = '$feature' ".
		    "	GROUP BY 1 ".
		    ") SELECT * FROM foo GROUP BY 1,2 ORDER BY 1";
		    
	my $domain = $dbh->selectall_hashref($query,1)
		or die "Unable to retrieve domain [$start:$end]+[$curr]";
	#print Dumper($domain);
	debug "$dtxt Retrieve domain [$start:$end]",V;
	return $domain;
}


# return the complete reference set in form of |time|var|feature| (sort by <time,var>)
# given a time range [$tstart:$tend] and a tollerated size of the distributions in
# [$size_min:$size_max]. Only not anomalous distributions are returned
sub getRefSet {
	my ($self,$tstart,$tend,$size_min,$size_max,$rw_warn) = @_;
	
	my $dbh = $self->{_dbh};
	my $feat_tab = $self->{_feat};
	my $flag_tab = $self->{_flags};
	my $feat = $self->{_fname};
	my $var  = $self->{_var};
	
	my $query =	"WITH foo AS (" .
			#"	SELECT serial_time, COUNT(DISTINCT $var) AS cnt ".
			"	SELECT serial_time, sum(feature_value) AS cnt ".
			"	FROM $feat_tab ".
			"	WHERE serial_time BETWEEN $tstart AND $tend AND ".
			"		feature_name = '$feat'".
			"	GROUP BY 1 ".
			"), ".
			"tbin_list AS ( ".
			"	SELECT f.serial_time ".
			"	FROM foo f, $flag_tab fl ".
			"	WHERE	f.serial_time = fl.serial_time AND ".
			"		cnt BETWEEN $size_min AND $size_max ";
	$query.=	"		AND (code = 0)" unless $rw_warn;
	$query.=	") ".
			"SELECT l.serial_time, $var as variable, feature_value as feature ".
			"FROM tbin_list l, $feat_tab f ".
			"WHERE l.serial_time = f.serial_time AND f.feature_name = '$feat' ".
			"ORDER BY 1,2";
			
	my $res_query = $dbh->selectall_arrayref($query)
			or die "Unable to retrieve reference set in [$tstart:$tend]";
	my $res = {};
	foreach my $row (@$res_query) {
		my ($st,$var1,$feat) = @$row;
		#$var1="NULL" unless $var1;
		$res->{$st}->{$var1}->{'feature'} = $feat; # possibly a bug on $var (already defined). try fix with $var1
	}
		
	debug "$dtxt Retrieve RefSet (distrib. with size in [$size_min,$size_max]): ".scalar(keys %$res),V;
	#print Dumper($res);
	return $res;
}

# create the flags table with name specified in config file
# if it does not already exists, otherwise do nothing
sub createFlagsTable {
	my ($self) = @_;
	my $dbh = $self->{_dbh};
	my $table = $self->{_flags};

	my $create =
		"CREATE TABLE IF NOT EXISTS $table ( ".
		"	serial_time integer, ".
		"	feature_name varchar(30), ".
		"	code int2, ".
		"	score float4, ".
		"	gamma float4, ".
		"	phi_alpha float4, ".
		"	CONSTRAINT key_$table ".
		"    PRIMARY KEY (serial_time, feature_name) ".
		")";
	
	my $result = eval {
		my $sth = $dbh->prepare($create);
		   $sth->execute;
		1;
	};
	
	debug "$dtxt Flags table correctly set",V;

	return 1;
}

# create the drift table with name specified in config file
# if it does not already exists, otherwise do nothing
sub createDriftTable {
	my ($self) = @_;
	my $dbh = $self->{_dbh};
	my $table = $self->{_drifts};

	# delete table if it exists
	my $drop =  "DROP TABLE $table";
	my $result = eval {
		my $sth = $dbh->prepare($drop);
		   $sth->execute;
		1;
	};

	my $create =
		"CREATE TABLE IF NOT EXISTS $table ( ".
		"	serial_time integer, ".
		"	variable_name varchar(60), ".
		"	feature_name varchar(30), ".
		"	current bigint, ".
		"	average bigint, ".
		"	drift bigint ,".
		"	CONSTRAINT key_$table ".
		"    PRIMARY KEY (serial_time, variable_name, feature_name) ".
		")";
	
	$result = eval {
		my $sth = $dbh->prepare($create);
		   $sth->execute;
		1;
	};
	
	debug "$dtxt Drift table correctly set",V;

	return 1;
}



# return the last classified time-bin contained in the flags table
# or 0 if the flags table is empty
sub getLastClassifiedBin {
	my ($self) = @_;
	my $dbh = $self->{_dbh};
	my $table = $self->{_flags};
	my $feature = $self->{_fname};
	
	my $query = "SELECT serial_time ".
				"FROM $table ".
				"WHERE feature_name='$feature' ".
				"ORDER BY 1 DESC ".
				"LIMIT 1";

	my $last_ts = $dbh->selectrow_arrayref($query) or 0;
	if (!$last_ts or $last_ts == 0) {
		debug "$dtxt Warning: flags table empty", V;
	}
	else {
		debug "$dtxt Last classified bin: $last_ts->[0]",V;
	}
	return $last_ts->[0];
}


# return the first available time bin in features table
sub getFirstFeaturesTimeBin {
	my ($self) = @_;
	my $dbh = $self->{_dbh};
	my $table = $self->{_feat};
	my $feature = $self->{_fname};

	my $query = "SELECT serial_time ".
				"FROM $table ".
				"WHERE feature_name='$feature' ".
				"GROUP BY 1 ".
				"ORDER BY 1 ASC ".
				"LIMIT 1";

	my $first_ts = $dbh->selectrow_arrayref($query) or 0;
	if($first_ts == 0) {
		die "[$dtxt] [ERROR!!] Features table is empty. Exit.";
	}
	return $first_ts->[0];
}

# return the first available time bin in features table
sub getLastFeaturesTimeBin {
	my ($self) = @_;
	my $dbh = $self->{_dbh};
	my $table = $self->{_feat};
	my $feature = $self->{_fname};

	my $query = "SELECT serial_time ".
				"FROM $table ".
				"WHERE feature_name='$feature' ".
				"GROUP BY 1 ".
				"ORDER BY 1 DESC ".
				"LIMIT 1";

	my $last_ts = $dbh->selectrow_arrayref($query) or 0;
	if($last_ts == 0) {
		die "ERROR! Features table is empty";
	}
	return $last_ts->[0];
}

# given a feature name, a time range (start-end) and a time
# granularity, execute a fake training (all time slots in the
# specified range are set with code 0-normal)
sub executeFakeTraining {
	my ($self,$start,$end,$gran) = @_;
	my $dbh = $self->{_dbh};
	my $feat_tab  = $self->{_feat};
	my $flags_tab = $self->{_flags};
	my $feature = $self->{_fname};

	my $query = "INSERT INTO $flags_tab ( ".
				"	SELECT serial_time-serial_time\%$gran, ".
				"		   '$feature', 0, 0, 0, 0 ".
				"	FROM $feat_tab ".
				"	WHERE serial_time BETWEEN $start and $end ".
				"	GROUP BY 1,2,3 ".
				"	ORDER BY 1 ".
				")";

	my $sth = $dbh->prepare($query)->execute 
		or die "Error in executing 'fake training'\n";

	debug "$dtxt Executing fake training $start-$end",V;
}







# check if features table contain data corresponding to the 
# specified time-bin
sub check_availability {
	my ($self,$timestamp) = @_;
	my $dbh		= $self->{_dbh};
	my $feat_tab	= $self->{_feat};
	my $feature	= $self->{_fname};
	my $query = "SELECT count(*) ".
		    "FROM $feat_tab ".
		    "WHERE serial_time = $timestamp AND feature_name = '$feature' ";
	my $count_row = $dbh->selectrow_arrayref($query);
	debug "$dtxt Check if data available",V;
	return $count_row->[0];
}

# check if a time bin has been already classified against specific feature name
# (i.e. there is a correspondent row in flags table)
sub check_if_classified {
	my ($self,$timestamp,) = @_;
	my $dbh = $self->{_dbh};
	my $flag_tab = $self->{_flags};
	my $feature = $self->{_fname};
	my $query = "SELECT code ".
		    "FROM $flag_tab ".
		    "WHERE serial_time = $timestamp AND feature_name = '$feature'";
	my $res  = $dbh->selectrow_arrayref($query);
	my $code = ($res) ? $res->[0] : -1;
	debug "$dtxt Check if $timestamp already classified: code=$code",V;
	return $code;
}

# disconnect from database
sub disconnect {
	my ($self) = @_;
	my $dbh = $self->{_dbh};
	my $dbname = $self->{_dbname};

	$dbh->disconnect or die "Error in disconnecting from databaser\n";
	debug "$dtxt Disconnected from database '$dbname'",V;
}

# function for the alarming in Darwin
sub alarming_update {
	my ($self,$alarm,$pre_duration_integer,$pre_score_threshold,
	    $ctime, $refkey, $title, $description, $sendprofileid) = @_;
	    
	debug "$dtxt Updating alarm with code $alarm...",V;
	
	my $dbh = $self->{_dbh};
	my $feature = $self->{_fname};
	my $flag_tab = $self->{_flags};
	my $drift_tab = $self->{_drifts};
	
	my $plots;

	my $enkl_sql =	"SELECT serial_time as time, gamma as curr_dist, phi_alpha as up_bound ".
				"FROM $flag_tab ".
				"WHERE ".
				" serial_time BETWEEN $ctime-(3600*48) AND $ctime ".
				"ORDER BY 1";

	my $enkl_opt = "name=enkld_trend,xlabel=time,ylabel=ENKLd,xdate=1,legend=1";
	
	my $tab_sql = "SELECT * ".
			"FROM $drift_tab ".
			"WHERE serial_time BETWEEN \$1-(3600*24) AND \$2"	;
	
	my $tab_opt = "name=drift_vars,xdate=1";
	
	my $driftlist_sql = "SELECT variable_name, avg(drift) as average_drift ".
			"FROM $drift_tab ".
			"WHERE serial_time BETWEEN \$1-(3600*24) AND \$2 ".
			"GROUP BY 1 ORDER BY 2";
	
	my $driftlist_opt = "name=drift_vars2";
	
	$plots = "'{".
		"\"time-series|$enkl_sql|$enkl_opt\"".",".
		"\"table|$tab_sql|$tab_opt\"".",".
		"\"table|$driftlist_sql|$driftlist_opt\"".
	"}'";
	
	
	my $call = "SELECT alarming_update(".
	    "$alarm,$pre_duration_integer,$pre_score_threshold,".
	    "$ctime,'$refkey','$title','$description','$sendprofileid',$plots)";
		   	
	my $sth = $dbh->prepare($call)->execute 
		or die "Error in calling alarming_update function'\n";

	debug "$dtxt Correctly called alarming_update on database\n",V;
	
}

# update an existing result code (flag) for a specified time-bin
# and feature
sub update_drift {
	my ($self,$timebin,$drifts) = @_;

	my $target = $self->{_drifts};
	my $dbh    = $self->{_dbh};
	my $feature = $self->{_fname};
	
	foreach my $var (keys %$drifts) {
		my ($drift,$curr,$avg) = (
			$drifts->{$var}->{'drift'},
			$drifts->{$var}->{'current'},
			$drifts->{$var}->{'average'}
		);
		
		my $sql = "INSERT INTO $target VALUES ".
			"($timebin,'$var','$feature',$curr,$avg,$drift)";
		
		my $sth = $dbh->prepare($sql);
		   $sth->execute or die $!;
	}
	
	debug "$dtxt Reporting drifting variable for timbin=$timebin on DB",V;
	return;
}


1;
