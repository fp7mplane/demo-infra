#!/usr/bin/perl

# Search for public RIPE Atlas custom measurements
# Author: Pierdomenico Fiadino <fiadino@ftw.at>

## modules ##

use warnings;
use strict;
use diagnostics;
use Getopt::Long;
use Pod::Usage;
use LWP::Simple;
use Data::Dumper;
use JSON;

## variables ##

my ($help);
my ($type,$status,$is_oneoff);
my ($dst_addr,$dst_name,$dst_asn);
my ($start,$stop,$creation_time);
my ($probes,$interval);

## get options ##

my $rc = GetOptions(
	"help"		=> \$help,
	"type=s"	=> \$type,
	"status"	=> \$status,
	"start=s"	=> \$start,
	"stop=s"	=> \$stop,
	"creation=s"=> \$creation_time,
	"probes=s"	=> \$probes,
	"is-oneoff" => \$is_oneoff,
	"interval=i"=> \$interval,
	"dst-addr=s"=> \$dst_addr,
	"dst-name=s"=> \$dst_name,
	"dst-asn=s" => \$dst_asn,
	
) or die "Syntax error: $!";

## print help ##

if ($help) {
	pod2usage(2);
}

## request url ##

my $domain = "https://atlas.ripe.net";
my $atlas_url = "$domain/api/v1/measurement/?";
my $filters = "";
if($type)	{ $filters.="type=$type&" }
if($is_oneoff)  { $filters.="is_oneoff=$is_oneoff&" }
if($stop)       { $filters.="stop_time=$stop&" }
if($start)	{ $filters.="start_time=$start&" }
if($probes)	{ $filters.="probe_source=$probes&" }
if($dst_addr)	{ $filters.="dst_addr=$dst_addr&" }
if($dst_name)	{ $filters.="dst_name=$dst_name&" }

my $next_url = $atlas_url.$filters;

## iterative request ##

while($next_url) {

	my $crnt_json = get $next_url;
	my $crnt_hash = from_json $crnt_json;

	my $crnt_meta = $crnt_hash->{'meta'};
	my $crnt_objs = $crnt_hash->{'objects'};

	&print_objects($crnt_objs);
	#print Dumper($crnt_objs);

	if($crnt_meta->{'next'}) {
		$next_url = $domain.$crnt_meta->{'next'};
	}
	else {
		$next_url = 0;
	}
}

## exit loop and exit script

exit 0;

## subroutines ##

sub print_objects {
	my ($objects) = @_;
	foreach my $obj (@$objects) {
		my $udm_id      = $obj->{'msm_id'};
		my $udm_type    = $obj->{'type'}->{'name'};
		my $udm_status  = $obj->{'status'}->{'name'}; 

		my $udm_interval= ($obj->{'interval'}) ? $obj->{'interval'} : 0;
		my $udm_isoneoff= ($obj->{'is_oneoff'}) ? $obj->{'is_oneoff'} : 0;

		my $udm_start = $obj->{'start_time'};
		my $udm_stop  = ($obj->{'stop_time'}) ? $obj->{'stop_time'} : 0;

		my $udm_dst_addr = $obj->{'dst_addr'};
		my $udm_dst_name = $obj->{'dst_name'};
		my $udm_dst_asn  = $obj->{'dst_asn'};

		print "$udm_id\t$udm_type\t$udm_status\t".
			  "$udm_start\t$udm_stop\t$udm_interval\t".
			  "$udm_dst_name\t$udm_dst_addr\t$udm_dst_asn\t".
			  "\n";
	}
}

__END__

=pod

=head1 NAME

=head1 VERSION

=head1 DESCRIPTION

=head1 SYNOPSIS

	perl udm-lookup [OPTIONS]

If not options are specified, it will print all available measurements
sorted by UDM ID (don't do that).

=head2 Options

=over 12

=item B<--help>

show help

=item B<--type=<ping|dns|traceroute|sslcert>>

filter results by measurement type 

=item B<--status=<CODE>>

filter results by status code

=item B<--is-oneoff>

get 'one-off' measurement only

=item B<--dst-addr=<IP>>

filter results by destination address

=item B<--dst-name=<NAME>>

filter results by destination name

=item B<--dst-asn=<ASN>>

filter results by destination A.S.

=item B<--start=<TIMESTAMP>>

filter results by start time

=item B<--stop=<TIMESTAMP>>

filter results by stop time

=item B<--creation=<TIMESTAMP>>

filter results by measurement creation time

=back

=head1 LICENSE

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>

=head1 ACKNOWLEDGEMENT

This work has been partially funded by the European Commission 
funded mPlane ICT-318627 project (www.ict-mplane.eu).

=head1 AUTHOR

Pierdomenico Fiadino <fiadino@ftw.at>

Vienna - May, 2014

=cut

