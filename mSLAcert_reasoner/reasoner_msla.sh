#!/bin/bash
#This is a simple reasoner for SLA verification, it makes use of an mPlane clinet to connect to the supervisor.
#
#			Dev: Edion TEGO (FUB) 2015
#
###########################################################################################################
###$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##
###$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$     $$$$$$$$  $$$$$$       $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##
##$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$  $$$  $$$$$$  $$$$$  $$$$$  $$$$$$  $$$$$$$$$$$$$$    $$$$$$$$##
##$$$$$$$$$$$$$      $$$$$$$$$$$$$$$$$$$$$  $$$$$  $$$$  $$$$  $$$$$$$  $$$$$        $$$$$$  $$$$  $$$$$$##
##$$$$$$$$$$   ;$$$$   $$$$$$       $$$$$$  $$$$  $$$$$  $$$$$$$$$   $  $$$$$  $$$$$  $$$$  $$$$$  $$$$$$##
##$$$$$$$$   $$$$$$$$  $$$$   $$$$$  $$$$$  $$  $$$$$$$  $$$$$$$  $$$$  $$$$$  $$$$$  $$$$        $$$$$$$##
##$$$$$$   $$$$$$$$$$!      $$$$$$$   $$$$   $$$$$$$$$$  $$$$$  $$$$$$  $$$$$  $$$$$  $$$$  $$$$$$$$$$$$$##
##$$$$   $$$$$$$$$$$$$$  $$$$$$$$$$$  $$$$  $$$$$$$$$$$  $$$$  $$$$$    $$$$$  $$$$$  $$$$  $$$$$  $$$$$$##
##$$$  $$$$$$$$$$$$$$$$$$$$$$$$$$$$$  $$$$  $$$$$$$$$$$  $$$$$       $  $$$$$  $$$$$  $$$$$       $$$$$$$##
###$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##
##$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##
###$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##
###$$$$$$$$_____________________&______________________&_____________&_______________$$$$$$$$$$$$$$$$$$$$##
###$$$$$$$|Politecnico di Torino|Fondazione Ugo Bordoni| SSB Progetti| Telecom Italia|&$$$$$$$$$$$$$$$$$$##
###$$$$$$$$---------------------&----------------------&-------------&---------------$$$$$$$$$$$$$$$$$$$$##
##$$$$________________________&_______&_________________&_______________$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##
###$$|Alcatel-Lucent Bell Labs|EURECOM| Telecom Paritech| NEC Europe LTD| $$$$$$$$$$$$$$$$$$$$$$$$] && [] && [&$$##
###$$$------------------------&-------&-----------------&---------------$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##
##$$________________________________________&________&_____________________________________________$$$$$$##
###|Telefonica Investigacion Y Desarrollo Sa|Netvisor|Forschungszentrum Telekommunikation Wien Gmbh|$$$$$##
###$----------------------------------------&--------&---------------------------------------------$$$$$$##
##$$$$$$$$_______________________&____________________&_____________________________________________$$$$$##
##$$$$$$$|Fachhochschule Augsburg||Universite de Liege|Eidgenoessische Technische Hochschule Zurich |$$$$##
###$$$$$$$-----------------------&--------------------&---------------------------------------------$$$$$##
###$$$$$$$$$$$$$$$$$$$$$$$______________________&_______$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##
###$$$$$$$$$$$$$$$$$$$$$$|Alcatel-Lucent Bell Nv|FASTWEB|$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
###$$$$$$$$$$$$$$$$$$$$$$$----------------------&-------$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##
###$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$|mPlane Supervisior|$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##
###########################################################################################################
###                            Keep calm, the Reasoner is running ^_^                                   ###

notify-send -t 1200 Reasoner_mSLA_has_stared_results_in_PDF_shortly
close_cycle=1;
check_var=1;
repeat20=0;
retrys20=0;
rowipaddressdest=1;
udp=0;
tcp=0;
ping=0;
while [ $check_var -eq 1 ]
do

ipaddressdest=$(expr `cat ./ipaddressdest.in | awk NR==$rowipaddressdest`);
if [ $ipaddressdest -eq 010001010100111101000110 ]
then	notify-send -t 1200 Finished_controlling_all_IPs
 	exit
else
fi
ipsupervisor=$(expr `cat ./ipsupervisor.in`);
timemeas=$(expr `cat ./timemeas.in| awk 'NR==1 {print $1}'`);
measnum=$(expr `cat ./measnum.in`);


echo "Launching RTT, TCP and UDP test!"
./reasoner_check.exp $ipaddressdest $timemeas $measnum $ipsupervisor> ./result_check_$ipaddressdest.txt
pingmin=`cat ./result_check_$ipaddressdest.txt| awk 'NR==26 {print $2}'|awk '{print int($1)}'`;
pingmean=`cat ./result_check_$ipaddressdest.txt| awk 'NR==27 {print $2}'|awk '{print int($1)}'`;
pingmax=`cat ./result_check_$ipaddressdest.txt| awk 'NR==28 {print $2}'|awk '{print int($1)}'`;
pingsamples=`cat ./result_check_$ipaddressdest.txt| awk 'NR==29 {print $2}'|awk '{print int($1)}'`;
tcpmin=`cat ./result_check_$ipaddressdest.txt| awk 'NR==30 {print $2}'|awk '{print int($1)}'`;
tcpmean=`cat ./result_check_$ipaddressdest.txt| awk 'NR==31 {print $2}'|awk '{print int($1)}'`;
tcpmax=`cat ./result_check_$ipaddressdest.txt| awk 'NR==32 {print $2}'|awk '{print int($1)}'`;
tcpsamples=`cat ./result_check_$ipaddressdest.txt| awk 'NR==33 {print $2}'|awk '{print int($1)}'`;
udpmin=`cat ./result_check_$ipaddressdest.txt| awk 'NR==34 {print $2}'|awk '{print int($1)}'`;
udpmean=`cat ./result_check_$ipaddressdest.txt| awk 'NR==35 {print $2}'|awk '{print int($1)}'`;
udpmax=`cat ./result_check_$ipaddressdest.txt| awk 'NR==36 {print $2}'|awk '{print int($1)}'`;
udpsamples=`cat ./result_check_$ipaddressdest.txt| awk 'NR==37 {print $2}'|awk '{print int($1)}'`;
udpjitter=`cat ./result_check_$ipaddressdest.txt| awk 'NR==38 {print $2}'|awk '{print int($1)}'`;
udperror=`cat ./result_check_$ipaddressdest.txt| awk 'NR==39 {print $2}'|awk '{print int($1)}'`;
udpclient=`cat ./result_check_$ipaddressdest.txt| awk 'NR==40 {print $2}'|awk '{print int($1)}'`;

empty=0

if [ "$empty$pingmin" = "$empty" ]
then echo "Could not get min Ping data!"
fi
if [ "$empty$pingmean" = "$empty" ]
then echo "Could not get mean Ping data!"
fi
if [ "$empty$pingmax" = "$empty" ]
then echo "Could not get max Ping data!"
fi
if [ "$empty$pingsamples" = "$empty" ]
then echo "Could not get samples Ping data!"
fi
if [ "$empty$tcpmin" = "$empty" ]
then echo "Could not get min TCP data!"
fi
if [ "$empty$tcpmean" = "$empty" ]
then echo "Could not get mean TCP data!"
fi
if [ "$empty$tcpmax" = "$empty" ]
then echo "Could not get max TCP data!"
fi
if [ $tcpmax -gt 99 ]
then tcpmax=99
fi
if [ "$empty$tcpsamples" = "$empty" ]
then echo "Could not get samples TCP data!"
fi
if [ "$empty$udpmin" = "$empty" ]
then echo "Could not get min UDP data!"
fi
if [ "$empty$udpmean" = "$empty" ]
then echo "Could not get mean UDP data!"
fi
if [ "$empty$udpmax" = "$empty" ]
then echo "Could not get max UDP data!"
fi
if [ "$empty$udpsamples" = "$empty" ]
then echo "Could not get samples UDP data!"
fi
if [ "$empty$udpjitter" = "$empty" ]
then echo "Could not get jitter UDP data!"
fi
if [ "$empty$udperror" = "$empty" ]
then echo "Could not get error UDP data!"
fi
if [ "$empty$udpclient" = "$empty" ]
then echo "Could not get UDP client data!"
fi

if [ [ "$empty$tcpmean" = "$empty" ] && [ "$empty$udpmean" = "$empty" ] && [ "$empty$udpclient" = "$empty" ] ]
then echo "Could not get any data, possible issue: the destination agent is down!"
fi

./udp_check.exp $ipaddressdest $timemeas $measnum $ipsupervisor> ./udp_check_$ipaddressdest.txt
udpmin2=`cat ./udp_check_$ipaddressdest.txt| awk 'NR==26 {print $2}'|awk '{print int($1)}'`;
udpmean2=`cat ./udp_check_$ipaddressdest.txt| awk 'NR==27 {print $2}'|awk '{print int($1)}'`;
udpmax2=`cat ./udp_check_$ipaddressdest.txt| awk 'NR==28 {print $2}'|awk '{print int($1)}'`;
udpjitter2=`cat ./udp_check_$ipaddressdest.txt| awk 'NR==29 {print $2}'|awk '{print int($1)}'`;
udperror2=`cat ./udp_check_$ipaddressdest.txt| awk 'NR==30 {print $2}'|awk '{print int($1)}'`;
udpclient2=`cat ./udp_check_$ipaddressdest.txt| awk 'NR==31 {print $2}'|awk '{print int($1)}'`;
udpsamples2=`cat ./udp_check_$ipaddressdest.txt| awk 'NR==32 {print $2}'|awk '{print int($1)}'`;

while [ [ $udpclient -eq -1 ] && [ $retrys20 -lt 3 ] && [ $udpclient2 -eq -1 ] ]
do
	echo "Could not retrive the client data, will repeat only the UDP test"
	./udp_check.exp $ipaddressdest $timemeas $measnum $ipsupervisor> ./udp_check_2_$ipaddressdest.txt
	udpmin2=`cat ./udp_check_2_$ipaddressdest.txt| awk 'NR==26 {print $2}'|awk '{print int($1)}'`;
	udpmean2=`cat ./udp_check_2_$ipaddressdest.txt| awk 'NR==27 {print $2}'|awk '{print int($1)}'`;
	udpmax2=`cat ./udp_check_2_$ipaddressdest.txt| awk 'NR==28 {print $2}'|awk '{print int($1)}'`;
	udpjitter2=`cat ./udp_check_2_$ipaddressdest.txt| awk 'NR==29 {print $2}'|awk '{print int($1)}'`;
	udperror2=`cat ./udp_check_2_$ipaddressdest.txt| awk 'NR==30 {print $2}'|awk '{print int($1)}'`;
	udpclient2=`cat ./udp_check_2_$ipaddressdest.txt| awk 'NR==31 {print $2}'|awk '{print int($1)}'`;
	udpsamples2=`cat ./udp_check_2_$ipaddressdest.txt| awk 'NR==32 {print $2}'|awk '{print int($1)}'`;
	udp=1;
	if [ $udpclient2 -eq -1 ]
	then retrys20=$(( retrys20+1 ))
		echo "Could not retrive the client data, will repeat tests in 20 minutes"
		sleep 20m
	fi
done

if [ "$empty$udpmin2" = "$empty" ]
then echo "Could not get min UDP data-2°test!"
fi
if [ "$empty$udpmean2" = "$empty" ]
then echo "Could not get mean UDP data-2°test!"
fi
if [ "$empty$udpmax2" = "$empty" ]
then echo "Could not get max UDP data-2°test!"
fi
if [ "$empty$udpsamples2" = "$empty" ]
then echo "Could not get samples UDP data-2°test!"
fi
if [ "$empty$udpjitter2" = "$empty" ]
then echo "Could not get jitter UDP data-2°test!"
fi
if [ "$empty$udperror2" = "$empty" ]
then echo "Could not get error UDP data-2°test!"
fi
if [ "$empty$udpclient2" = "$empty" ]
then echo "Could not get UDP client data-2°test!"
udpclient2=-0
fi

if [ $udpclient2 -eq -1 ]
	then
		echo "After two retries could not retrieve the client data,every test will be repeated according to the settings set by admin!"
		
	fi

./tcp_check.exp $ipaddressdest $timemeas $measnum $ipsupervisor> ./tcp_check_$ipaddressdest.txt
tcpmin2=`cat ./tcp_check_$ipaddressdest.txt| awk 'NR==26 {print $2}'|awk '{print int($1)}'`;
tcpmean2=`cat ./tcp_check_$ipaddressdest.txt| awk 'NR==27 {print $2}'|awk '{print int($1)}'`;
tcpmax2=`cat ./tcp_check_$ipaddressdest.txt| awk 'NR==28 {print $2}'|awk '{print int($1)}'`;
tcpsamples2=`cat ./tcp_check_$ipaddressdest.txt| awk 'NR==29 {print $2}'|awk '{print int($1)}'`;

if [ $tcpmax2 -gt 99 ]
then tcpmax2=99
fi

tcpvalidation=$(( tcpmax - tcpmin ));
tcpvalidation1=$(echo "scale=2; ($tcpmean/10)" | bc)
tcpvalidation2=$(( tcpmax2 - tcpmin2 ));
tcpvalidation12=$(echo "scale=2; ($tcpmean2/10)" | bc)

if [ [ $tcpvalidation -gt $tcpvalidation1 ] && [ $tcpvalidation2 -gt $tcpvalidation12 ] ]
	echo "Will repeat TCP test, to much variation into throughput values of the first test!"
	then ./tcp_check.exp $ipaddressdest $timemeas $measnum $ipsupervisor> ./tcp_check_2_$ipaddressdest.txt
	tcpmin2=`cat ./tcp_check_2_$ipaddressdest.txt| awk 'NR==26 {print $2}'|awk '{print int($1)}'`;
	tcpmean2=`cat ./tcp_check_2_$ipaddressdest.txt| awk 'NR==27 {print $2}'|awk '{print int($1)}'`;
	tcpmax2=`cat ./tcp_check_2_$ipaddressdest.txt| awk 'NR==28 {print $2}'|awk '{print int($1)}'`;
	tcpsamples2=`cat ./tcp_check_2_$ipaddressdest.txt| awk 'NR==29 {print $2}'|awk '{print int($1)}'`;
	tcp=1;
fi

if [ $tcpmax2 -gt 99 ]
then tcpmax2=99
fi

if [ "$empty$tcpmin2" = "$empty" ]
then echo "Could not get min TCP data-2°test!"
fi
if [ "$empty$tcpmean2" = "$empty" ]
then echo "Could not get mean TCP data-2°test!"
fi
if [ "$empty$tcpmax2" = "$empty" ]
then echo "Could not get max TCP data-2°test!"
fi
if [ "$empty$tcpsamples2" = "$empty" ]
then echo "Could not get samples TCP data-2°test!"
fi

./ping_check.exp $ipaddressdest $timemeas $measnum $ipsupervisor> ./ping_check_$ipaddressdest.txt
pingmin2=`cat ./ping_check_$ipaddressdest.txt| awk 'NR==26 {print $2}'|awk '{print int($1)}'`;
pingmean2=`cat ./ping_check_$ipaddressdest.txt| awk 'NR==27 {print $2}'|awk '{print int($1)}'`;
pingmax2=`cat ./ping_check_$ipaddressdest.txt| awk 'NR==28 {print $2}'|awk '{print int($1)}'`;
pingsamples2=`cat ./ping_check_$ipaddressdest.txt| awk 'NR==29 {print $2}'|awk '{print int($1)}'`;

pingvalidation=$(( pingmax - pingmin ));
pingvalidation1=$(echo "scale=2; ($pingmean/2)" | bc)
pingvalidation2=$(( pingmax2 - pingmin2 ));
pingvalidation12=$(echo "scale=2; ($pingmean2/2)" | bc)

if [ [ $pingvalidation -gt $pingvalidation1 ] && [ $pingvalidation2 -gt $pingvalidation12 ] ]
	echo "Will repeat Ping test!"
	then ./ping_check.exp $ipaddressdest $timemeas $measnum $ipsupervisor> ./ping_check_2_$ipaddressdest.txt
	pingmin2=`cat ./ping_check_2_$ipaddressdest.txt| awk 'NR==26 {print $2}'|awk '{print int($1)}'`;
	pingmean2=`cat ./ping_check_2_$ipaddressdest.txt| awk 'NR==27 {print $2}'|awk '{print int($1)}'`;
	pingmax2=`cat ./ping_check_2_$ipaddressdest.txt| awk 'NR==28 {print $2}'|awk '{print int($1)}'`;
	pingsamples2=`cat ./ping_check_2_$ipaddressdest.txt| awk 'NR==29 {print $2}'|awk '{print int($1)}'`;
	ping=1;
fi

if [ "$empty$pingmin2" = "$empty" ]
then echo "Could not get min Ping data-2°test!"
fi
if [ "$empty$pingmean2" = "$empty" ]
then echo "Could not get mean Ping data-2°test!"
fi
if [ "$empty$pingmax2" = "$empty" ]
then echo "Could not get max Ping data-2°test!"
fi
if [ "$empty$pingsamples2" = "$empty" ]
then echo "Could not get samples Ping data-2°test!"
fi

plotping=0;
pingrow=43;
if [ $ping -eq 1 ]
then
	while [ $plotping -lt $pingsamples2]
	do
	echo $plotping>> timeping_$ipaddressdest.txt
	pingvalues=`cat ./ping_check_2_$ipaddressdest.txt| awk NR==$pingrow | awk '{print $2}'`
	echo $pingvalues>> pingvalues_$ipaddressdest.txt
	pingrow=$(( pingrow+3 ))
	plotping=$(( plotping+1 ))
	done
else
while [ $plotping -lt $pingsamples2]
	do
	echo $plotping>> timeping_$ipaddressdest.txt
	pingvalues=`cat ./ping_check_$ipaddressdest.txt| awk NR==$pingrow | awk '{print $2}'`
	echo $pingvalues>> pingvalues_$ipaddressdest.txt
	pingrow=$(( pingrow+3 ))
	plotping=$(( plotping+1 ))
done
fi


plottcp=0;
tcprow=43;
if [ $tcp -eq 1 ]
then
	while [ $plottcp -lt $tcpsamples2]
	do
	echo $plottcp>> timetcp_$ipaddressdest.txt
	tcpvalues=`cat ./tcp_check_2_$ipaddressdest.txt| awk NR==$tcprow | awk '{print $2}'`
	if [ $tcpvalues -gt 99 ]
	then tcpvalues=99
	fi
	echo $tcpvalues>> tcpvalues_$ipaddressdest.txt
	tcprow=$(( tcprow+3 ))
	plottcp=$(( plottcp+1 ))
	done
else
while [ $plottcp -lt $tcpsamples2]
	do
	echo $plottcp>> timetcp_$ipaddressdest.txt
	tcpvalues=`cat ./tcp_check_$ipaddressdest.txt| awk NR==$tcprow | awk '{print $2}'`
	if [ $tcpvalues -gt 99 ]
	then tcpvalues=99
	fi
	echo $tcpvalues>> tcpvalues_$ipaddressdest.txt
	tcprow=$(( tcprow+3 ))
	plottcp=$(( plottcp+1 ))
done
fi

plotudp=0;
udprow=46;
if [ $udp -eq 1 ]
then
	while [ $plotudp -lt $udpsamples2]
	do
	echo $plotudp>> timeudp_$ipaddressdest.txt
	udpvalues=`cat ./udp_check_2_$ipaddressdest.txt| awk NR==$udprow | awk '{print $2}'`
	echo $udpvalues>> udpvalues_$ipaddressdest.txt
	udprow=$(( udprow+6 ))
	plotudp=$(( plotudp+1 ))
	done
else
while [ $plotudp -lt $udpsamples2]
	do
	echo $plotudp>> timeudp_$ipaddressdest.txt
	udpvalues=`cat ./udp_check_$ipaddressdest.txt| awk NR==$udprow | awk '{print $2}'`
	echo $udpvalues>> udpvalues_$ipaddressdest.txt
	udprow=$(( udprow+6 ))
	plotudp=$(( plotudp+1 ))
done
fi

gnuplot -persist
set style data linespoints
show timestamp
set output "RTT_$ipaddressdest.png"
set title "RTT evolution in microsec for ip: $ipaddressdest"
set xlabel "Time (seconds)"
set ylabel "Value in microseconds"
set key right bottom
set term png size 640,480
plot "./pingvalues_$ipaddressdest.txt" using $1 title "RTT"
set style data linespoints
show timestamp
set output "TCP_$ipaddressdest.png"
set title "TCP Throughput evolution in mbps for ip: $ipaddressdest"
set xlabel "Time (seconds)"
set ylabel "Value in mbps"
set key right bottom
set term png size 640,480
plot "./tcpvalues_$ipaddressdest.txt" using $1 title "RTT"
set style data linespoints
show timestamp
set output "UDP_$ipaddressdest.png"
set title "UDP Throughput evolution in mbps for ip: $ipaddressdest"
set xlabel "Time (seconds)"
set ylabel "Value in mbps"
set key right bottom
set term png size 640,480
plot "./udpvalues_$ipaddressdest.txt" using $1 title "RTT"

rm ./pingvalues_$ipaddressdest.txt
rm ./tcpvalues_$ipaddressdest.txt
rm ./udpvalues_$ipaddressdest.txt

echo -------------- REPORT FOR RTT fo Ip $ipaddressdest----------------->>ping_report_$ipaddressdest.output
echo ------------------------------------------------------------------->>ping_report_$ipaddressdest.output
echo ------------------------------------------------------------------->>ping_report_$ipaddressdest.output
echo ----The minimum RTT observed during two diferent tests was--------->>ping_report_$ipaddressdest.output
echo ----------    $pingmin usec and $pingmin2 usec    ----------------->>ping_report_$ipaddressdest.output
echo ------------------------------------------------------------------->>ping_report_$ipaddressdest.output
echo -----The mean RTT observed during two diferent tests was----------->>ping_report_$ipaddressdest.output
echo ------------    $pingmean usec and $pingmean2 usec  --------------->>ping_report_$ipaddressdest.output
echo ------------------------------------------------------------------->>ping_report_$ipaddressdest.output
echo ------The max RTT observed during two diferent tests was----------->>ping_report_$ipaddressdest.output
echo ------------    $pingmax usec and $pingmax2 usec    --------------->>ping_report_$ipaddressdest.output
echo ------------------------------------------------------------------->>ping_report_$ipaddressdest.output
echo ----Below is the evolution in, time of RTT------------------------->>ping_report_$ipaddressdest.output
echo ------------------------------------------------------------------->>ping_report_$ipaddressdest.output

echo ----------- REPORT FOR TCP throughput of Ip $ipaddressdest--------->>tcp_report_$ipaddressdest.output
echo ------------------------------------------------------------------->>tcp_report_$ipaddressdest.output
echo ------------------------------------------------------------------->>tcp_report_$ipaddressdest.output
echo -The minimum TCP throughput observed during two diferent tests was->>tcp_report_$ipaddressdest.output
echo ------------    $tcpmin usec and $tcpmin2 usec    ----------------->>tcp_report_$ipaddressdest.output
echo ------------------------------------------------------------------->>tcp_report_$ipaddressdest.output
echo --The mean TCP throughput observed during two diferent tests was--->>tcp_report_$ipaddressdest.output
echo ------------    $tcpmean usec and $tcpmean2 usec  ----------------->>tcp_report_$ipaddressdest.output
echo ------------------------------------------------------------------->>tcp_report_$ipaddressdest.output
echo ---The max TCP throughput observed during two diferent tests was--->>tcp_report_$ipaddressdest.output
echo -------------    $tcpmax usec and $tcpmax2 usec    ---------------->>tcp_report_$ipaddressdest.output
echo ------------------------------------------------------------------->>tcp_report_$ipaddressdest.output
echo -----Below is the evolotion ,in time of TCP throughput ------------>>tcp_report_$ipaddressdest.output
echo ------------------------------------------------------------------->>tcp_report_$ipaddressdest.output

echo ----------- REPORT FOR UDP throughput of Ip $ipaddressdest--------->>udp_report_$ipaddressdest.output
echo ------------------------------------------------------------------->>udp_report_$ipaddressdest.output
echo ------------------------------------------------------------------->>udp_report_$ipaddressdest.output
echo -The minimum UDP throughput observed during two diferent tests was->>udp_report_$ipaddressdest.output
echo ------------    $udpmin usec and $udpmin2 usec    ----------------->>udp_report_$ipaddressdest.output
echo ------------------------------------------------------------------->>udp_report_$ipaddressdest.output
echo --The mean UDP throughput observed during two diferent tests was--->>udp_report_$ipaddressdest.output
echo ------------    $udpmean usec and $udpmean2 usec  ----------------->>udp_report_$ipaddressdest.output
echo ------------------------------------------------------------------->>udp_report_$ipaddressdest.output
echo ---The max UDP throughput observed during two diferent tests was--->>udp_report_$ipaddressdest.output
echo -------------    $udpmax usec and $udpmax2 usec    ---------------->>udp_report_$ipaddressdest.output
echo ------------------------------------------------------------------->>udp_report_$ipaddressdest.output
echo -----Below is the evolotion ,in time of UDP throughput ------------>>udp_report_$ipaddressdest.output
echo ------------------------------------------------------------------->>udp_report_$ipaddressdest.output


cupsfilter ping_report_$ipaddressdest.output > ping_report_$ipaddressdest.pdf
cupsfilter tcp_report_$ipaddressdest.output > tcp_report_$ipaddressdest.pdf
cupsfilter udp_report_$ipaddressdest.output > udp_report_$ipaddressdest.pdf
convert RTT_$ipaddressdest.png > RTT_$ipaddressdest.pdf
convert TCP_$ipaddressdest.png > TCP_$ipaddressdest.pdf
convert UDP_$ipaddressdest.png > UDP_$ipaddressdest.pdf

convert ping_report_$ipaddressdest.pdf RTT_$ipaddressdest.pdf tcp_report_$ipaddressdest.pdf TCP_$ipaddressdest.pdf udp_report_$ipaddressdest.pdf UDP_$ipaddressdest.pdf > Report_for_$ipaddressdest.pdf

rm ping_report_$ipaddressdest.output
rm tcp_report_$ipaddressdest.output
rm udp_report_$ipaddressdest.output
rm ping_report_$ipaddressdest.pdf
rm tcp_report_$ipaddressdest.pdf
rm udp_report_$ipaddressdest.pdf
rm RTT_$ipaddressdest.png
rm TCP_$ipaddressdest.png
rm UDP_$ipaddressdest.png
rm RTT_$ipaddressdest.pdf
rm TCP_$ipaddressdest.pdf
rm UDP_$ipaddressdest.pdf


rowipaddressdest=$(( rowipaddressdest+1 ))
ipaddressdest=$(expr `cat ./ipaddressdest.in | awk NR==$rowipaddressdest`);
if $ipaddressdest -eq 010001010100111101000110
then check_var=2
fi
done
