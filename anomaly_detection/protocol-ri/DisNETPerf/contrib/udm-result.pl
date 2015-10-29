#!/usr/bin/perl

# Ger results of a RIPE Atlas measurement
# Author: Pierdomenico Fiadino <fiadino@ftw.at>


### modules ###

use warnings;
use strict;
use diagnostics;
use JSON;
use Pod::Usage;
use LWP::Simple;
use LWP::UserAgent;
use HTTP::Request;
use Getopt::Long;
use Data::Dumper;
use MIME::Base64;
use Net::DNS::Packet;

### variables ###

my $help;
my $udm_id; 
my $api_key;
my $latest;
my ($start,$stop);

### read options ###

my $rc = GetOptions(
	"help"		=>\$help,
	"udm-id=i"	=>\$udm_id,
	"api-key=s"	=>\$api_key,
	"latest"	=>\$latest,
	"start=i"	=>\$start,
	"stop=i"	=>\$stop
) or die "Syntax error";

### print help

if($help) {
	pod2usage(1);
}

### check arguments ###

if(!$udm_id) {
	die "Missing argument: --udm is mandatory"
}

### submit requested ###

my $url = "https://atlas.ripe.net/api/v1/measurement/$udm_id/result/?";
if($start) { $url.="start=$start&" }
if($stop)  { $url.="stop=$stop&"   }

if($latest) {
	#TO-DO
}

else {	
	##my $udm_result_json = get $url;
	my $request   = HTTP::Request->new('GET' => $url);
    my $ua = LWP::UserAgent->new;
    my $response = $ua->request($request);
    my $udm_result_json = $response->content;
	my $udm_result_array = from_json $udm_result_json or exit 1;

	for my $result (@$udm_result_array) {
		print_result($result);		
	}
}

exit 0;

### subroutines ###

# print a line  of results with UDMtype-specific format
sub print_result {
	my ($res) = @_;
	##print Dumper($res);
	# read measurement type
	my $type = $res->{'type'};
	
	# read probe-related info
	my $timestamp= $res->{'timestamp'} || "NA";
	my $prb_id   = $res->{'prb_id'} || "NA";
	my $from     = $res->{'from'} || "NA";
	my $probe = "$timestamp\t$prb_id\t$from";

	# if type is ping, print result line(s) accordingly
	if($type eq "ping") {
		my $dst_addr = $res->{'dst_addr'} || "NA";
		my $dst_name = $res->{'dst_name'} || "NA";
		my $res_set = $res->{'result'};
		foreach my $ping (@$res_set) {
			my $rtt = $ping->{'rtt'} || "*";
			print "$probe\t$dst_name\t$dst_addr\t$rtt\n";
		}
	}

	# if type is dns, print result line(s) accordingly
	elsif($type eq "dns") {
		my $res_set = $res->{'resultset'};
		foreach my $dns (@$res_set) {
			my $dst_addr = $dns->{'dst_addr'};
			my $abuf = $dns->{'result'}->{'abuf'};
			my $dec_buff = decode_base64 $abuf;
			if(defined $abuf && defined $dec_buff) {
				my ($dns_pack)= new Net::DNS::Packet(\$dec_buff);
				my @ans = $dns_pack->answer;
				foreach my $ans (@ans) {
					my $res_ip = $ans->{'address'} || '*';
					my $res_ttl = $ans->{'ttl'} || '*';
					my $req_name = $ans->{'name'} || '*';
					print "$probe\t$dst_addr\t".
					      "$req_name\t$res_ip\t$res_ttl\n";
				}
			}
		}
	}
	
	# if type is traceroute, print result line(s) accordingly
	 elsif($type eq "traceroute") {
                my $dst_addr = $res->{'dst_addr'} || "NA";
                my $dst_name = $res->{'dst_name'} || "NA";
                my $res_set  = $res->{'result'};
                my $hop_count= scalar @$res_set;
                #print "$probe\t$dst_name\t$dst_addr\t$hop_count\n";
                my @res_buffer;
                foreach my $hop (@$res_set) {
                        my $hop_num = $hop->{'hop'};
                        my $hop_set = $hop->{'result'};
                        my $avg_rtt = 0; my $pack_count = 0;
                        my ($from_ip,$ttl,$rtt);
                        foreach my $hop_step (@$hop_set) {
                                $from_ip = $hop_step->{'from'} || '*';
                                $ttl     = $hop_step->{'ttl'} || '*';
                                $rtt     = $hop_step->{'rtt'} || '0';
                                $avg_rtt += $rtt;
                                $pack_count++;
                        }
                        $avg_rtt = ($avg_rtt>0) ? ($avg_rtt/$pack_count)
                        : '*';
                        #print "\t$hop_num\t$from_ip\t$ttl\t$avg_rtt\n";
                        if(defined $from_ip && defined $ttl && defined
                        $avg_rtt) {
                                push @res_buffer,
                                "\t$hop_num\t$from_ip\t$ttl\t$avg_rtt\n";
                        }
                }
                if(scalar(@res_buffer) > 0) {
                        print
                        "$probe\t$dst_name\t$dst_addr\t$hop_count\n";
                        foreach my $res (@res_buffer) {
                                print $res;
                        }
                }
        }

	else {
		die "UDM type $type is currenty unsupported"
	}
}


__END__

=head1 NAME

udm-result	-	Get a measurement result from RIPE Atlas in CSV

=head1 DESCRIPTION

Get a text tab-separated result of a User Defined Measurement (UDM)
from the RIPE Atlas platform using the REST APIs. 
If the measurement is private, an API key with suitable permissions
has to be provided.

By default, the program gets all available results associated
to a measurement. It is also possible to refine the query in 
a specified time range or just get the latest available result.

The results have different have different output format depending
on the measurement type, as showed below:

=head2 ping output fields (tab-separated)

	timestamp | probe_id | probe_ip | dst_name | dst_addr | rtt

=head2 dns output fields (tab-separated)

	timestamp | probe_id | probe_ip | dns_server | req_name | res_ip | ttl

=head2 traceroute output fields (tab-separated)

	timestamp | probe_id | probe_ip | dst_name | dst_addr | hop_count
		hop_num | hop_ip | ttl | avg_rtt

=head1 SYNOPSIS

Usage: udm-result [OPTIONS]...

=head2 Options

=over 12

=item B<--help>

show help

=item B<--udm=<ID>> I<(mandatory)>

the ID of the measurement

=item B<--api-key=<KEY>>

the API key (could be needed for private measurements)

=item B<--latest>

retrieve only latest results

=item B<--start=<TIMESTAMP>>, --stop=<TIMESTAMP>>

retrieve results in specific time-range

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
