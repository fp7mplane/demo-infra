#!/usr/bin/perl
use warnings;
use strict;

use ADTool::Configs;
use JSON;
use HTTP::Request::Common;
use Getopt::Long;
use Data::Dumper;
use LWP::UserAgent;

$|++;

use Log::Message::Simple qw /debug/;
my $dtxt = "[ADTool::testing] ";

my $config_file;
my $help;

my $opt = GetOptions(
	"config=s" => \$config_file,
	"help"	   => \$help
);

if(!$opt || $help || !$config_file) {
	print STDERR "Usage: [cmd] --config=adtoolconfig.xml\n";
	exit 1;
}

my $adconf = ADTool::Configs->new($config_file);


# populate an hash table with 256**2 fake local IPs
my $drifts;


sub get_random_ip {
	my $num = shift;
	my $res;
	for (my $i = 0; $i < $num; $i++) {
		my $rand_ip = (int(rand(256))+1) . "." . 
			(int(rand(254))+1) . "." .
			(int(rand(254))+1) . "." .
			(int(rand(254))+1) ;
		$res->{$rand_ip} = 1;
	}
	return $res;
}



debug "$dtxt Start loop",1;
debug "",1;
my $ua = LWP::UserAgent->new;

while(1) {

	my $this_time = time;

	debug "$dtxt Simulating execution in $this_time",1;

	my $superv_addr = $adconf->getSupervisor;
	my %json_hash;
	debug "$dtxt Sending to $superv_addr",1;
	$json_hash{'time'}  = $this_time;
	$json_hash{'code'}  = 1;
	$json_hash{'score'} = rand(2);
	$json_hash{'dist'}  = rand(2);
	$json_hash{'bound'} = rand(2);
	my $drifts = get_random_ip(int(rand(9))+1);
	my @elem_list = keys %$drifts;
	$json_hash{'list'}  = \@elem_list;
	my $json = encode_json \%json_hash;
	my $req = HTTP::Request->new( 'POST' => $superv_addr );
	$req->header( 'Content-Type' => 'application/json' );
	$req->content( $json );
	my $resp = $ua->request($req);
    if ($resp->is_success) {
        my $message = $resp->decoded_content;
        print "Received reply: $message\n";
    }
    else {
        print "HTTP POST error code: ", $resp->code, "\n";
        print "HTTP POST error message: ", $resp->message, "\n";
    }
	
	debug "$dtxt Fake JSON sent: $json",1;
	debug "",1;
	debug "",1;

	sleep 1200;
}
