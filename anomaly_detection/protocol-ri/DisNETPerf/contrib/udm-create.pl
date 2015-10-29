#!/usr/bin/perl

# udm-create -- Create a custom measurement on RIPE Atlas platform
# Author: Pierdomenico Fiadino <fiadino@ftw.at>



### modules ###

use strict;
use warnings;
use diagnostics;

use JSON;
use Getopt::Long;
use LWP::UserAgent;
use HTTP::Request;
use Data::Dumper;
use Pod::Usage;



### declare arguments ###

my $help;

# probes-related arguments
my ($probe_list,$probe_file,@probes);

# common arguments
my $api_key;
my ($start,$stop,$interval);
my ($type,$target,$descr,$af);
my ($res_on_probe,$private);

# dns specific arguments
my ($dns_arg,$dns_class,$dns_type);

# ping and traceroute specific args
my ($packets);

# dns and traceroute specific args
my ($proto);



### read arguments ###

my $rc = GetOptions(
	"help"			=>\$help,
	"api-key=s"		=>\$api_key,
	"probe-list=s"		=>\$probe_list,
	"probe-file=s"		=>\$probe_file,
	"start=i"		=>\$start,
	"stop=i"		=>\$stop,
	"interval=i"		=>\$interval,
	"af=i"			=>\$af,
	"type=s"		=>\$type,
	"description=s"		=>\$descr,
	"target=s"		=>\$target,
	"resolve-on-probe"	=>\$res_on_probe,
	"private"		=>\$private,
	"dns-arg=s"		=>\$dns_arg,
	"dns-type=s"		=>\$dns_type,
	"dns-class=s"		=>\$dns_class,
	"packets=i"		=>\$packets,
	"protocol=s"		=>\$proto
) or die "Syntax error";


### print help ###

if($help) {
	pod2usage(2);
}

### check if mandatory are present ###

if(!$api_key) {
	die "Missing argument: --api-key is mandatory"
}

if(!$type) { 
	die "Missing argument: --type is mandatory" 
}

if(($type eq "traceroute" || $type eq "ping") && !$target) {
	die "Missing argument: --target is mandatory for ping/traceroute"
}

if($type eq "dns" && !$dns_arg) {
	die "Missing argument: --dns-arg is mandatory for dns"
}

### check allowed values ###

if($type ne "dns" && $type ne "ping" && $type ne "traceroute") {
	die "Error: unknown type ($type). Use dns, ping or traceroute"
}

if($proto && $type eq "traceroute" &&
	$proto ne "ICMP" && $proto ne "TCP" && $proto ne "UDP") {
	die "Error: unknown protocol ($proto) for traceroute. Use TCP/UDP/ICMP"
}

if($proto && $type eq "dns" && $proto ne "TCP" && $proto ne "UDP") {
	die "Error: unknown protocol ($proto) for dns. Use TCP/UDP"
}

if($dns_type && $type eq "dns" && $dns_type ne "A" && $dns_type ne "CNAME") {
	die "Error: unknown type ($type). Use 'A' or 'CNAME'"
}

if($af && $af != 4 && $af != 6) {
	die "Error: unknown address family ($af). Use 4 for IPv4 or 6 for IPv6"
}



### check temporal constraints ###

if($start && !$stop) {
	die "Error: if --start is used, also --stop must be present"
}
if($start && ($stop<=$start || $stop-$start<60)) {
	die "Error: stop time must be greater than start time of at least 60s"
}
if($interval && $interval < 60) {
	die "Error: Interval must be greater than 60 seconds"
}



### set defaults ###

if($type eq "traceroute" && !$proto) {
	$proto = "ICMP";
}

if($type eq "dns" and !$dns_class) {
	$dns_class = "IN";
}

if($type eq "dns" and !$dns_type) {
	$dns_type = "A";
}

if(!$af) {
	$af = 4;
}

if(!$descr) {
	$descr = ($target)? "target=$target " : "";
	if($type eq "dns") { $descr.= "resolve=$dns_arg " }
	if($start)         { $descr.= "[$start:$stop]"    }
	else	           { $descr.= "one-off"		  }
}



### read probes ###

if($probe_list) {
	@probes = split /,/,$probe_list;
}
elsif($probe_file) {
	open PF, "<", $probe_file or die $!;
	@probes= <PF>;
}
elsif(! (-t STDIN)) {
	@probes= <>;
}
else {
	die "Error: provide a list of probe IDs with ".
		"--probe-file, --probe-list or to the STDIN\n";
}
if(@probes<1) {
	die "Error: empty probe list\n";
}
@probes = map {($_) = split /\t/,$_} @probes;



### wrap up request JSON ###

# json scheleton
my $container;

# common options
$container->{'definitions'}->[0]->{'type'} = $type;
$container->{'definitions'}->[0]->{'description'} = $descr;
$container->{'definitions'}->[0]->{'af'} = $af;
if($target) { # remember that it is not mandatory for dns
	$container->{'definitions'}->[0]->{'target'} = $target
}
if($private) {
	$container->{'definitions'}->[0]->{'is_public'} = "false"
}
if($res_on_probe) {
	$container->{'definitions'}->[0]->{'resolve_on_probe'} = "true"
}

# time constraints
if($start and $stop) {
	$container->{'start_time'} = $start;
	$container->{'stop_time'}  = $stop;
}
else {
	$container->{'definitions'}->[0]->{'is_oneoff'} = "true"
}

if($interval) {
	$container->{'definitions'}->[0]->{'interval'} = $interval
}


# dns specific options
if($type eq "dns") {
	$container->{'definitions'}->[0]->{'query_class'}    = $dns_class;
	$container->{'definitions'}->[0]->{'query_type'}     = $dns_type;
	$container->{'definitions'}->[0]->{'query_argument'} = $dns_arg;
	if(!$target) {
		$container->{'definitions'}->[0]->{'use_probe_resolver'} = 
			"true"
	}
}

# protocol (for dns and traceroute)
if($proto) {
	$container->{'definitions'}->[0]->{'protocol'} = $proto; 
}

# number of packets (for ping and traceroute)
if($packets)  { 
	$container->{'definitions'}->[0]->{'packets'} = $packets; 
}

# probes part
$container->{'probes'}->[0]->{'requested'} = scalar @probes;
$container->{'probes'}->[0]->{'type'} = "probes";
$container->{'probes'}->[0]->{'value'} = join(",",@probes);



### submit json ###

my $udm_json = to_json $container;
my $dumb = from_json $udm_json;
my $atlas_url = "https://atlas.ripe.net/api/v1/measurement/?key=$api_key";
my $request   = HTTP::Request->new('POST' => $atlas_url);
   $request->header('Content-Type' => 'application/json');
   $request->content($udm_json);
my $ua = LWP::UserAgent->new;
my $response = $ua->request($request);



### check response ###

if($response->is_success) {
	my $dec_content = $response->decoded_content;
	my ($msm_list) = $dec_content =~ m/\[(.*)\]/;
	print join("\n",(split /,/,$msm_list));
	print "\n";
	exit 0;
}
else {
	print STDERR "Error submitting UDM json: ".$response->status_line."\n";
	print STDERR "POST URL: $atlas_url\n";
	print STDERR "JSON content: ";
	print STDERR Dumper($dumb);
	print STDERR "Message: " . $response->decoded_content . "\n";
	exit 1;
}




__END__

=pod

=head1 NAME

udm-create	-	Create a custom User Defined Measurement on RIPE Atlas

=head1 VERSION

1.0

=head1 DESCRIPTION

This program allows to set a custom measurement on RIPE Atlas platform
using RIPE's REST APIs. To set-up a User Defined Measurement (UDM), an
API KEY with 'Measurement creation' permissions is required.

Available measurement types are: ping, dns and traceroute.

A DNS UDM instruments Atlas boxes to resolve
an hostname (i.e. query-argument) using a specified DNS server or
the probe's default resolver. The query type can be A, AAAA or CNAME.

The list of probes that will run the UDM must be provided either with
the --probe-file or --probe-list argument. The first allows to load
a file containing a list of probe IDs one per row 
(e.g. --probe-file my_probe_list.txt), the latter allows to specify 
a comma-separated list of probes (e.g. --probe-list 5234,134,1235).
A list of probes (one-per-row) can be also passed to the STDIN, usefull
in pipe with the B<probe_list.pl> program, e.g.:

 ./probe_list --country it --limit 3 | ./udm-create.pl --query-arg example.com --api 123

An UDM can be 'one-off' (i.e. executed just once) or executed periodically
in a specified time-window (see --start, --stop, --interval options).

A DNS query uses UDP protocol by default. TCP is also possibile using
--protocol TCP option.

For a full list of options, see 'Options' section below.

=head1 SYNOPSIS

Usage: perl udm-create.pl [OPTIONS]...

=head3 Generic options

=over 12
	
=item B<--help>

show help

=item B<--api-key=<KEY>> I<(mandatory)>

an API key with 'Measurement creation' permissions

=item B<--type=<dns|ping|traceroute>> I<(mandatory)>

type of measurement (supported ping/traceroute/dns)

=item B<--target=<TARGET>> I<(mandatory)>

for ping/traceroute, it is the target of measurement;
for dns it is the resolver (use probe's resolver if not specified)

=item B<--private> 

if used, the measurement will be private

=item B<--probe-file=<FILE> or --probe-list=<id1,id2,..>> I<(mandatory)>

load a list of probes from file or pass a CSV list

=item B<--start=<time>, --stop=<time>, --interval=<seconds>>

start, stop timestamps for the measurement and interval in seconds
(if not specified, run a one-off measurement)

=item B<--protocol=<PROTOCOL>>

for traceroute can be ICMP/TCP/UDM; for dns can be UDP/TCP
(un-used for ping)

=item B<--packets=<NUM_OF_PACKETS>>

number of packets to send for traceroute and ping
(un-used for dns)

=back

=head3 DNS-specific options

=over 12

=item B<--dns-arg=<ARG>> I<(mandatory)>

the hostname to resolve (eg. www.example.com)

=item B<--dns-class=<IN|CHAOS>>

the class of the DNS query (default 'IN')

=item B<--query-type=<A|CNAME>>

the DNS query type (default 'A')

=back

=head1 Requirements

This program require the Perl interpreter (which comes with most systems)
and the libjson-perl library (for the REST APIs).

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
