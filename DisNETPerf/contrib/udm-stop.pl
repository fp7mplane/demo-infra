#!/usr/bin/perl

# Stop a RIPE Atlas measurement
# Author: Pierdomenico Fiadino <fiadino@ftw.at>


# required modules
use strict;
use warnings;
use diagnostics;
use Getopt::Long;
use HTTP::Request;
use LWP::UserAgent;
use Data::Dumper;
use Pod::Usage;
use JSON;

# read options
my ($help,$udmid,$apikey);
my $rc = GetOptions (
	"help"		=> \$help,
	"udm-id=i"	=> \$udmid,
	"api-key=s"	=> \$apikey
) or die "Syntax error";

# print help
if ($help) {
	pod2usage(1);
}

# check mandatory options
if(!$udmid or !$apikey) {
	die "Arguments --udm-id and --api-key are mandatory.\n";
}

# measurement URL
my $udm_url  = "https://atlas.ripe.net/api/v1/measurement/$udmid/?key=$apikey";

my $http_req = HTTP::Request->new('DELETE' => $udm_url);
my $lwp_ua   = LWP::UserAgent->new;
my $http_res = $lwp_ua->request($http_req);

if($http_res->is_success) {
	print "Measurement $udmid has been successfully stopped.\n";
	exit 0;
}
else {
	print STDERR "Error in stopping UDM $udmid.\n";
	print STDERR "Remote message: " . $http_res->{_msg} . "\n";
	exit 1;
}


__END__

=pod

=head1 NAME

udm-stopstop	-	Stop a User Defined Measurement (UDM) on RIPE Atlas

=head1 SYNOPSIS

perl udm-stop.pl [OPTIONS]...

=head2 OPTIONS

=over 12

=item B<--udm=<ID>>

the ID of the measurement to stop (mandatory)

=item B<--api-key=<KEY>>

the API key with stop permissions (mandatory)

=item B<--help>	

show help

=back

=head1 DESCRIPTION

This Perl script stops a running User Defined Measurement (UDM) on RIPE Atlas using 
the rest APIs.
It requires the measurement ID and an API key with "Stopping a Measurement" permission.

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
