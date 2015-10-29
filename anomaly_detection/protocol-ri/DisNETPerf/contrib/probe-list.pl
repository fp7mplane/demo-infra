#!/usr/bin/perl


use warnings;
use strict;
use diagnostics;

# required modules
use Getopt::Long;
use LWP::Simple;
use JSON;
use Data::Dumper;
use Pod::Usage;
#use Geo::Coder::Googlev3; # debian package libgeo-coder-googlev3-perl


# instanciate required variables
my ($help);
our ($limit,$asn,$area,$country,$prefix,$status);
our ($coo,$addr,$radius,$lat,$lon);

# read options
my $rc = GetOptions (

	"help"			=> \$help,		# show this help
	"limit=i"		=> \$limit,		# limit number of results			# eg. --limit 10
	"asn=i"			=> \$asn,		# only probe in specific AS			# eg. --asn 1234
	"area=s"		=> \$area,		# CURRENTLY UNUSED					# eg. --area "ww"
	"country=s"		=> \$country,	# only probes in specific country	# eg. --country it
	"prefix=s"		=> \$prefix,	# only probes in specific subnet	# eg. --prefix 43.52/24
	"status=s"		=> \$status,	# filter by status (1/2/3)			# eg. --status 1 
	"coordinates=s"	=> \$coo,		# probes close to coordinates		# eg. --coordinates 46.1,16.2
	"address=s"		=> \$addr,		# probes close to address			# eg. --address "Karlsplatz 2, Vienna, Austria"
	"radius=s"		=> \$radius		# sensitivity in Km					# eg. --radius 10

) or die "Syntax error. Use --help for more info\n";

# show help
if ($help) {
	pod2usage(1);
}

# check requirements and formatting for --coo/--addr and --rad
unless((defined $coo || defined $addr) == (defined $radius)) {
	print STDERR "Syntax error:\n";
	print STDERR "if --coo or --addr are used, --radius is mandatory (and viceversa)\n";
	exit 1;
}
#/^-?\d+\.?\d*$/
if($coo) {
	unless($coo =~ /\d\,\d/) {
		print STDERR "Coordinates bad format ($coo).\n";
		print STDERR "It should be like --coo 48.23,16.41\n";
		exit 0;
	}
	($lat,$lon) = split /,/,$coo;
}
if($addr) {
	use Geo::Coder::Googlev3; # debian package libgeo-coder-googlev3-perl
	my $gc = Geo::Coder::Googlev3->new;
	my $loc = $gc->geocode(location => $addr);
	$lat = $loc->{'geometry'}->{'location'}->{'lat'};
	$lon = $loc->{'geometry'}->{'location'}->{'lng'};
	if (!$lat || !$lon) {
		print STDERR "Bad address format: could not find this address\n";
		exit 0;
	}
}

# check status of probes
if(defined $status && 
	($status ne "1" && $status ne "2" && $status ne "3" && $status ne "all")) {
	print STDERR "Status bad format ($status). Allowed values:\n";
	print STDERR "  '1'      (connected)    [default]\n";
	print STDERR "  '2'      (disconnected)\n";
	print STDERR "  '3'      (abandoned\n";
	print STDERR "  'all'    (no filters)\n\n";
	exit 0;
}

# check area argument
my %avail_areas = map {$_ => 1} qw/WW West North-Central South-Central North-East South-East/;
if($area and ! exists $avail_areas{$area}) {
	print STDERR "Error: unknown area $area. ".
	"Available areas are: ".join(", ",keys(%avail_areas))."\n";
}


# default options
unless($limit)  { $limit = 20000 }
unless($status) { $status= 1    }

# subroutines

sub geodist {
	my ($lat1, $lon1, $lat2, $lon2) = @_;
	my $PI = atan2(1,1) * 4; # define an accurate value for PI
	my $lat1rad = $lat1*$PI/180; 
	my $lon1rad=$lon1*$PI/180; 
	my $lat2rad=$lat2*$PI/180; 
	my $lon2rad=$lon2*$PI/180; # convert degrees to radians
	my $gamma=(sin($lat1rad)*sin($lat2rad)+cos($lat1rad)*cos($lat2rad)*cos(($lon2rad-$lon1rad)));
	return acos($gamma) * 6371; # calculate the distance. 6371 is earth radius;
	
}

sub acos {
	my($in) = sprintf("%0.15f",@_);
	my $out = atan2(sqrt(1 - $in**2), $in);
	return $out;
}

sub query {
	my ($url) = @_;
	my $json = get $url or die "Unable to get json from $url";
	my $hash = decode_json $json or die "Unable to decode json";
	return $hash;
}

sub print_object {
	my ($object) = @_;
	foreach my $field (keys %$object) {
		if(!$field or $field eq "") {
			$object->{$field} = "NA";
		}
	}
	unless($object->{'address_v4'}) {
		$object->{'address_v4'} = "NA";
##		$object->{'asn_v4'}     = "NA";
##		$object->{'prefix_v4'}	= "NA";
	}
	unless($object->{'prefix_v4'}) {
		$object->{'prefix_v4'}  = "NA";
	}
	unless($object->{'asn_v4'}) {
		$object->{'asn_v4'} = "NA";
	}
#	unless($object->{'latitude'}) {
#		$object->{'latitude'}   = "NA";
#		$object->{'longitude'}  = "NA";
#	}
	print 	$object->{'id'}, 			"\t",
			$object->{'address_v4'}, 	"\t", 
			$object->{'prefix_v4'},		"\t",
			$object->{'asn_v4'}, 		"\t", 	
			$object->{'country_code'}, 	"\t", 
			$object->{'latitude'}, 		"\t", 
			$object->{'longitude'}, 	"\t", 
			$object->{'status'}, 		"\n"; 
}

sub evaluate_object {
	my ($object) = @_;

	if ($status ne "all" and $object->{'status'} != $status) {
		return 0;
	}
	
	if (($lat && $lon) && geodist($lat,$lon,$object->{'latitude'},$object->{'longitude'}) > $radius) {
		return 0;
	}

	return 1;
}

# prepare query url
my $fields = "fields=address_v4,asn_v4,prefix_v4,country_code,latitude,longitude,status,id";
my $domain   = "https://atlas.ripe.net";
my $base_url = $domain."/api/v1/probe/?$fields&";
my $qlimit = 30;

#my $query_url = $base_url."limit=$qlimit";
#if($limit)		{	$query_url.="limit=$limit&";			}
my $next = $base_url;
if($country)	{	$next.="country_code=$country&";	}
if($asn)		{	$next.="asn_v4=$asn&"; 				}
if($prefix)		{	$next.="prefix_v4=$prefix&";		}
if($area)		{	$next.="area=$area&";				}

my @obj_list;
while($next && scalar(@obj_list)<$limit) {	

	my $probe_hash = query $next;

	my $meta    = $probe_hash->{'meta'};
	my $objects = $probe_hash->{'objects'};
	
	foreach my $object (@$objects) {
		if(scalar(@obj_list) >= $limit) {
			last;
		}
		if($object && evaluate_object($object)) {
			push @obj_list, $object;
			print_object $object;
		}
	}

	if($meta->{'next'}) {
		$next = $domain.$meta->{'next'};
	}
	else {
		$next = 0;
	}
}

exit 0;

__END__
=pod

=head1 NAME

probe_list	-	retrive lists of RIPE Atlas probes

=head1 DESCRIPTION

Retrieve a list of RIPE Atlas probes using the rest APIs.
The results can be refined with many filters, e.g.:
by country, by subnet, by autonomous system.

Additionally, it is possible to search for probes in a
geographical area specifing the coordinates <lat,lon> (WSG84 format) 
or a human readable address (e.g. "Piazza di Spagna, Roma")
along with a radius in Km.

If geographical filters (--coo or --addr with --radius) are used,
it is a good practice to use --country too. This speeds up the script.

By default, only 'connected' (status code '1') probes will be showed.
It is possible to get disconnected (code '2') and abandoned (code '3')
probes using the --status options and specifying the corresponding 
code (default '1').

For a complete list of available filters check the SYNOPSIS section
or use the --help option.

=head2 Output

The output is printed on the standard output as a list of tab-separated
values. The format of the rows is:

 probe_id | probe_IP | subnet | asn | country | lat | lon | status_code

=head2 Requirements

This script uses JSON objects for the Atlas rest APIs. The JSON module
can be installed through CPAN or by installing the package
'libjson-perl' on Debian/Ubuntu systems.

For resolving the human readable address, the module Geo::Coder::Googlev3
is required. It is installable through the CPAN or installing 
the package 'libgeo-coder-googlev3-perl' on Debian/Ubuntu systems.

=head1 SYNOPSIS

Usage: perl probe_list.pl [OPTIONS]...

If no options are specified, it will print the full list of RIPE
Atlas probes (and you might not want it).

=head2 Options

=over 12

=item B<--help>

show help message

=item B<--asn>

get probes in a specified Autonomous System

=item B<--area>

fitler by geographical area

=item B<--country>

filter by country (2-digit codes, eg. it, at, uk, etc...)

=item B<--prefix>

filter by subnet (e.g. 54.17/16)

=item B<--status>

filter probes in a specific status (default 1 = active)

=item B<--coo>

filter probes by geo proximity to <lat,lon> (requires --radius)

=item B<--address>

filter probes by geo proximity to a human readable address (requires --radius)

=item B<--radius>

radius in Km required by --coordinates and --address

=item B<--limit>

limit the number of results (shoul be an integer)

=back

=head2 Examples

=over 12

=item (1) [cmd] --country at --coo 48.23,16.41 --radius 100 --limit 10

prints 10 probes in Austria (AT) at no more than 100Km from 48.23,16.41

=item (2) [cmd] --address "Rathausplatz, Vienna" --radius 10 --limit 5

prints 5 probes close (less than 10Km) to the specified address

=item (3) [cmd] --asn 1234 --filter 20

prints 20 probles in the Autonomous System 1234

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

=head1 AUTHOR

Pierdomenico Fiadino <fiadino@ftw.at>

=cut
