iGreedy -- Anycast Enumeration and Geolocation Module
-------------
iGreedy is a tool able to detect, enumerate and geolocate anycast replicas with a fistful of pings. 
This brief readme file describes the basic steps to get started with the tool. The tool
allows to:  
- **analyze** existing measurement 
- **generate** and analyze new measurement 
- **visualize** the measurement on a GoogleMap. 

The package also contains a datasets corredated with ground-truth to 
assess the accuracy of the tool.


Installation
-------------
iGreedy should run out of the box. There is no python depenedency which 
we are aware of. All the code you need is in the `code/` folder



Configuration
-------------
While running iGreedy on the provided datasets does not require any special
configuration, however to launch new measurement from RIPE Atlas you need to:
- have a *RIPE Atlas account*
- have *enough credits*
- configure your *authentication*. 
Measurement are launched by `code/RIPEAtlas.py` which is going
to read your RIPE Atlas key from the following file:

    datasets/auth

How to run iGreedy
-------------

     igreedy.py (-i input|-m target) [-o output] [-b browser (false)] 
                [-g groundtruth] [-a alpha (1)]  [-t threshold (\infty)] 

**Parameters:**

*mandatory:*

     -i input file
     -m IPV4 or IPV6 (real time measurements from Ripe Atlas using the ripe probes in datasets/ripeProbes) 

*optional:*

     -o output prefix (.csv,.json)
     -b browser (visualize a GoogleMap of the results in a browser)
     -g measured ground truth (GT) or publicly available information (PAI) files 
        (format: "hostname iata" lines for GT, "iata" lines for PAI)
     -a alpha (tune population vs distance score; was 0.5 in INFOCOM'15, now defaults to 1)
     -t threshold (discard disks having latency larger than threshold to bound the error; discouraged)


Example
-------------

Run iGreedy on existing measurement:
- over the F root server dataset, showing results on a map (opening your browser):

    `./igreedy -i datasets/measurement/f-ripe -b`

- over the F root server dataset, showing results and ground truth on a map (opening your browser):

    ./igreedy -i datasets/measurement/f-ripe -g ./igreedy -i datasets/ground-truth/f-ripe -b

- over the EdgeCast dataset, using publicly available information:

    `./igreedy -i datasets/measurement/edgecast-ripe -g datasets/public-available-information/edgecast `
    

Run iGreedy on new measurement from RIPE Atlas:
 
*Note1:* RIPE Atlas is instructed to vantage points contained in
            datasets/ripe-vps

*Note2:* You are free to use your favorite sets of vantage points by simply changing 
       the content of datasets/ripe-vps. We provide two example (ripe-vps.rand10 
       and ripe-vps.suggested200) that are conservative in the number of probes
       but useful for anecdotal use of:
        - detection (ripe-vps.rand10)
        - enumeration and geolocation (ripe-vps.suggested200)

*Note3:* The set of RIPE Atlas vantage points used by default (datasets/ripe-vps) is 
       conservative (10 random probes of ripe-vps.rand10) and useful at most for 
       detection (and to avoid burning all your credits with a for loop :)
       The set of ripe-vps.suggested200 is again very conservative and useful for 
       familiarizing with the tool before launching a measurement campaign. 

*Note4:* The set of measurements is saved in datasets/measurement for further post-processing

To run iGreedy on the F root server 192.5.5.241, configure your key (see above) then run:

       ./igreedy -m 192.5.5.241 -b
       
For more information and results at a glance [anycast project](http://perso.telecom-paristech.fr/~drossi/index.php?n=Dataset.Anycast) 
