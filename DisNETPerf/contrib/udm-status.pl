#!/usr/bin/perl

# Print status of a RIPE Atlas measurement
# Author: Pierdomenico Fiadino <fiadino@ftw.at>

## modules ##

use warnings;
use strict;
use diagnostics;
use JSON;
use LWP::Simple;
use Getopt::Long;
use Data::Dumper;
use Pod::Usage;

## variables ##

my $help;
my $api_key;
my $udm_id;

## read options ##

my $rc = GetOptions (
	"help"	   =>\$help,
	"api-key=s"=>\$api_key,
	"udm-id=i" =>\$udm_id
) or die "Syntax error";

## print help ##

if($help) {
	pod2usage(1);
}

## check arguments ##

unless($udm_id) {
	die "Missing argument: --udm-id is mandatory"
}

## retrieve measurement status ##

my $udm_url = "https://atlas.ripe.net/api/v1/measurement/$udm_id/";

if($api_key) {
	$udm_url.="?key=$api_key";
}

my $status_content = get $udm_url or die "Unable to download JSON";
my $status_hash = from_json $status_content or die "Unable to convert JSON";
$Data::Dumper::Varname = "UDM";
print Dumper($status_hash);

## exit

exit 0;

__END__

=pod

=head1 NAME

udm-status	-	retrieve status of a RIPE Atlas measurement

=head1 VERSION

1.0

=head1 DESCRIPTION

A simple script to retrieve the status of a RIPE Atlas measurement 
using RIPE'S REST APIs.
A suitable API key might be required depending on the measurement 
permissions.

=head1 SYNOPSIS

Usage: udm-status --udm=<ID> (--api=<KEY>)

API key is optional

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
