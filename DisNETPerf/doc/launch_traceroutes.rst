=====================
launch_traceroutes.py
=====================

| This script allows you to launch traceroutes from RIPE Atlas probes towards a given destination IP.
| To execute this script, use the following command:

.. code:: bash
 
 python launch traceroutes.py [-n <IP filename>] [-o <targetIP>] -d <dest IP> [-b <psBox ID>] -f f0, 1g [-m <nb traceroutes>] [-t <interval>] [-s <starttime>] [-p <stoptime>]

where:
    - -n <IP filename>: the name of the file containing the IP addresses which DisNETPerf should locate the closest probe for. **This file has to be stored in the 'input' folder.**
    - -o <targetIP>: the IP address which DisNETPerf should locate the proximity service box for
    - -d <dest IP>: the IP address the traceroute measurements are issued to
    - -b <psBox ID>: the ID of the probe the measurements should be launched from
    - -f {0, 1}: if set to 1, the proximity service box has to be already identified. If the parameter -n is used, the IDs of the boxes have to be indicated in the file; if -o is set, the ID has to be provided through the parameter -b. If the -f parameter is equal to 0, DisNETPerf first looks for the corresponding proximity service boxes before launching the traceroute measurements
    - -m <nb traceroutes>: the number of measurements to launch
    - -t <interval>: the time between two consecutive measurements, in seconds
    - -s <starttime>: the UNIX timestamp indicating when the first measurement should be issued
    - -p <stoptime>: the UNIX timestamp indicating when the last measurement should be launched

| Please note that, when you want to directly indicate the probes to be used within the file containing the different IP addresses, each line contains the IP address and the ID of the corresponding box (tab-separated).

| Moreover, DisNETPerf is quite flexible when it comes to the parameters -m, -t , and -s. Indeed, the following combinations are possible:

+-----+-----+-----+-----------------------------------+
|m    |t    |s    |behaviour                          |
+=====+=====+=====+===================================+
|X    |X    |X    |launch now one measurement         |
|     |     |     |(i.e. a on/off measurement)        |
+-----+-----+-----+-----------------------------------+
|O    |O    |X    |launch measurement now with        |
|     |     |     |stoptime = m * t                   |
+-----+-----+-----+-----------------------------------+
|O    |X    |NA   |launch measurement now (or at the  |
|     |     |     |indicated starttime)               | 
|     |     |     |and use the default interval       | 
|     |     |     |(= 600 secs)                       |  
+-----+-----+-----+-----------------------------------+

('X': parameter not used; 'O': parameter used; 'NA': don't care)