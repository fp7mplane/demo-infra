# mPlane mSLAcert reasoner
SLA reasoner is a script that controlls automatically the supervisor to request new measurements from the probes through a mplane RI client.mSLAcert reasoner will check automatically for RTT, TCP throughput and UDP throughput. To run mSLAcert reasoner are needed minimum two PCs and configured the sequent files:

ipaddressdest.in- each row contains the destination IP that have mSLAcert\_Agent enabled.
ipsupervisor.in- on this file is set the IP of the supervisor that the reasoner will use.
measnum.in- on this file is set the default value is "0", please do not change this file.
timemeas.in- on this file is set the time of the measurement in seconds, the default value is 40 seconds.
>>Requirements

Are needed as minimum requirement some linux tools:

	1. expect - sudo apt-get install expect

	2. iperf - sudo apt-get install iperf

	3. convert - sudo apt-get install imagemagick

	4. cupsfilter - sudo apt-get install cups
	
All the reasoner files need to be on the mother directory of mPlane RI code folder. To run the reasoner
you need first to add executable permission to the ".exp" files and to ".sh" file. Than from the terminal
set on the path of mother directory of the mPlane RI folder just run:

"./reasoner\_msla.sh"

After which the reasoner will automatically test all the destination IPs set on ipaddressdest.in file.
First the reasoner will make a test of RTT, TCP and UDP throughput all together. Than will test RTT, TCP and UDP singularly and will confront the results.

The main script is composed of four main parts, additional scripts. The first one "reasoner\_check.exp" will check all the requirements of SLA, RTT, TCP and UDP. The duration time will be divided by three, so each test will have one third, on "./reasoner\_msla.sh" this is presented as:

./reasoner\_check.exp \$ipaddressdest \$timemeas \$measnum \$ipsupervisor> ./result\_check\_\$ipaddressdest.txt

The other scripts "udp\_check.exp", "tcp\_check.exp" and "ping\_check.exp" will check UDP throughput, TCP throughput and RTT, the duration of each test will be as the three test all together of  "reasoner\_check.exp", on "./reasoner\_msla.sh" this is presented as::

./udp\_check.exp \$ipaddressdest \$timemeas \$measnum \$ipsupervisor> ./udp\_check\_\$ipaddressdest.txt
./tcp\_check.exp \$ipaddressdest \$timemeas \$measnum \$ipsupervisor> ./tcp\_check\_\$ipaddressdest.txt
./ping\_check.exp \$ipaddressdest \$timemeas \$measnum \$ipsupervisor> ./ping\_check\_\$ipaddressdest.txt

After every TCP test, the reasoner check if the measure is stable and that there isnt to much variation, if there is it will request an additional TCP check:

if [ [ \$tcpvalidation -gt \$tcpvalidation1 ] \&\& [ \$tcpvalidation2 -gt \$tcpvalidation12 ] ]
	echo "Will repeat TCP test, to much variation into throughput values of the first test!"
	then ./tcp\_check.exp \$ipaddressdest \$timemeas \$measnum \$ipsupervisor> ./tcp\_check\_2\_\$ipaddressdest.txt
	.....

TCP throughput it is also checked with UDP throughput, the throughput that the client sees:
if [ [ \$tcpudp -gt \$udptcp ] || [ \$tcpudp2 -gt \$udptcp ] || [ \$tcpudp21 -gt \$udptcp ] || [ \$tcpudp12 -gt \$udptcp ] ]
then echo "TCP bandwidth is more than 10\% lower than UDP bandwidth"
	./tcp\_check.exp \$ipaddressdest \$timemeas \$measnum \$ipsupervisor> ./tcp\_check\_2\_\$ipaddressdest.txt
    ....

After the reasoner has finished all the checks for all the IP addresses on "ipaddressdest.in", it will generate a PDF with the results of SLA, with mean value and the evolution in time for each IP.