# mPlane mSLAcert reasoner

mSLAcert reasoner is written in bash and expect script language, it automatically controls the supervisor 
by requesting new measurements. The reasoner checks RTT, TCP throughput and UDP throughput. To run mSLAcert reasoner are needed minimum two PCs.

### Software requirements

The following Linux tools are needed to be installed on the machine that will run the reasoner:

	1. expect - sudo apt-get install expect

	2. iperf - sudo apt-get install iperf

	3. convert - sudo apt-get install imagemagick

	4. cupsfilter - sudo apt-get install cups
	
### Files that need to be configured:

	ipaddressdest.in- On each row insert the destination IP of the PCs that have mSLAcert_Agent enabled.

	ipsupervisor.in- Insert the IP of the supervisor that the reasoner will use.

	timemeas.in- Duration of measurements in seconds, the default value is 40 seconds.


### Run the reasoner

Give executable permission to the ".exp" files and to ".sh" file and from the terminal set on the path of mother directory of the mPlane RI folder run the command:

		"./reasoner\_msla.sh"

This will launch the reasoner, which will store the data locally on a PDF of the mPlane RI directory.
