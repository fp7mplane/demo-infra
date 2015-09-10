SEARUM
======

Hadoop MapReduce implementation for Association Rule Mining technique.

Description
===========
Parallel FP-Growth and Association Rule mining MapReduce implementation. 

It runs each stage of PFPGrowth as described in the paper http://infolab.stanford.edu/~echang/recsys08-69.pdf, modified for and integrated with SEARUM as described in the paper http://www.ict-mplane.eu/sites/default/files/public/publications/386ispa2013grimaudo.pdf.

*Note*: the algorithm generate association rules with only a single item as a consequence

*The research leading to these results has received funding from the European Union under the FP7 Grant Agreement n. 318627 (Integrated Project "mPlane")*

Prerequisites
=============
- Java JDK 1.7
- Apache Maven

How to compile and build the jar
================================
- Download the code `git clone https://github.com/navxt6/SEARUM.git`
- Compile `mvn compile`
- Package the jar `mvn package`

How to run SEARUM
=================
Run SEARUM like this:

````java
hadoop jar searum-0.0.1-jar-with-dependencies.jar Searum \
  <input_file> \
  <output_directory> \
  <discretize (true|false)> \
  <min_sup (0.0-1.0)> \
  [<min_confidence (0.0-1.0)>]
````
Parameters:

  - *input_file*:  input transactional dataset
  - *output_directory*: output directory that holds intermediate and final results
  - *discretize*: true if you need a discretization step (you have to implement your own MapReduce job for that), false otherwise
  - *min_sup*: minimum support value for frequent itemset mining
  - *min_confidence*: minimum confidence value for association rule generation (optional)

Example
=======
In the data folder there is an example dataset already discretized that can be used to test SEARUM
- Create a directory on HDFS: `hadoop fs -mkdir searum_test`
- Create a sub-directory to hold the example dataset: `hadoop fs -mkdir searum_test/data`
- Upload the example dataset in HDFS: `hadoop fs -put data/example_dataset.dat`

Extract all frequent itemsets with minimum support 10%:
````java
hadoop jar target/searum-0.0.1-jar-with-dependencies.jar Searum searum_test/data/example_discretized.dat searum_test/output false 0.1
````

Visualize the top 10 most frequent itemsets (format ([itemset] \tab support_count - support):
`````
hadoop fs -cat searum_test/output/itemset_sorted/part-r-* | head -n 10

[P_REORDERING=0-0.1]    999 - 99.900%
[P_REORDERING=0-0.1, LOG_DATA_PACK_C=<1]        782 - 78.200%
[LOG_DATA_PACK_C=<1]    782 - 78.200%
[LOG_PACK_S=1-2]        724 - 72.400%
[P_REORDERING=0-0.1, LOG_PACK_S=1-2]    723 - 72.300%
[LOG_PACK_C=1-2]        693 - 69.300%
[P_REORDERING=0-0.1, LOG_PACK_C=1-2]    692 - 69.200%
[LOG_DATA_PACK_C=<1, LOG_PACK_S=1-2]    619 - 61.900%
[P_REORDERING=0-0.1, LOG_DATA_PACK_C=<1, LOG_PACK_S=1-2]        619 - 61.900%
[TCP_PORT_S=80] 579 - 57.900%
``````

Generate all association rules with minimum support 10% and minimum confidence 60%:
````java
hadoop jar target/searum-0.0.1-jar-with-dependencies.jar Searum searum_test/data/example_discretized.dat searum_test/output false 0.1 0.6
````

Visualize the association rules (format (rules \tab (support, confidence, lift)):
`````
hadoop fs -cat searum_test/output/rules/part-r-* | less

CLASS=HTTP LOG_PACK_C=<1 => LOG_DATA_PACK_C=<1  (0.136000, 1.000000, 1.278772)
CLASS=HTTP LOG_PACK_C=<1 => TCP_PORT_S=80       (0.136000, 1.000000, 1.727116)
CLASS=HTTP LOG_PACK_C=<1 => P_REORDERING=0-0.1  (0.136000, 1.000000, 1.001001)
CLASS=HTTP LOG_PACK_C=<1 => LOG_PACK_S=1-2      (0.101000, 0.742647, 1.025756)
LOG_BYTES_C=2-3 WINDOW_SCALE_S=2 => WIN_MIN_S=2*4k-4*4K (0.113000, 0.918699, 2.443349)
LOG_BYTES_C=2-3 WINDOW_SCALE_S=2 => LOG_PACK_S=1-2      (0.101000, 0.821138, 1.134169)
LOG_BYTES_C=2-3 WINDOW_SCALE_S=2 => P_REORDERING=0-0.1  (0.123000, 1.000000, 1.001001)
LOG_BYTES_C=2-3 WINDOW_SCALE_S=2 => LOG_DATA_PACK_C=<1  (0.123000, 1.000000, 1.278772)
LOG_BYTES_C=3-4 WINDOW_SCALE_S=2 => WIN_MAX_S=4*4k-8*4K (0.108000, 0.878049, 3.288572)
LOG_BYTES_C=3-4 WINDOW_SCALE_S=2 => LOG_PACK_C=1-2      (0.113000, 0.918699, 1.325684)
`````

Visualize the association rules aggregated by consequence (format (consequence \tab rules \tab (support, confidence, lift))
````
hadoop fs -cat searum_test/output/rules_aggregated/part-r-* | less

CLASS=HTTP	TCP_PORT_S=80 LOG_BYTES_S=4-5 WINDOW_SCALE_S=2 => CLASS=HTTP	(10.700%, 100%, 1.739)
CLASS=HTTP	LOG_PACK_C=1-2 TCP_PORT_S=80 LOG_BYTES_S=4-5 WIN_MIN_S=2*4k-4*4K => CLASS=HTTP	(10.300%, 100%, 1.739)
CLASS=HTTP	P_REORDERING=0-0.1 LOG_PACK_S=1-2 LOG_PACK_C=1-2 TCP_PORT_S=80 LOG_BYTES_C=3-4 LOG_DATA_PACK_S=1-2 LOG_BYTES_S=4-5 => CLASS=HTTP	(12.700%, 100%, 1.739)
CLASS=HTTP	P_REORDERING=0-0.1 LOG_PACK_C=1-2 TCP_PORT_S=80 WIN_MIN_S=2*4k-4*4K WINDOW_SCALE_S=2 => CLASS=HTTP	(13.500%, 100%, 1.739)
CLASS=HTTP	LOG_DATA_PACK_C=<1 LOG_PACK_S=1-2 TCP_PORT_S=80 WIN_MAX_S=4*4k-8*4K => CLASS=HTTP	(11.700%, 100%, 1.739)
CLASS=HTTP	P_REORDERING=0-0.1 LOG_PACK_C=1-2 TCP_PORT_S=80 WIN_MAX_S=4*4k-8*4K => CLASS=HTTP	(13.600%, 100%, 1.739)
CLASS=HTTP	TCP_PORT_S=80 LOG_DATA_PACK_S=1-2 WIN_MIN_S=2*4k-4*4K WINDOW_SCALE_S=2 => CLASS=HTTP	(10.200%, 100%, 1.739)
CLASS=HTTP	LOG_DATA_PACK_C=<1 LOG_PACK_S=1-2 LOG_PACK_C=1-2 TCP_PORT_S=80 WIN_MIN_S=4k-2*4K LOG_DATA_PACK_S=1-2 LOG_BYTES_S=4-5 => CLASS=HTTP	(11.700%, 100%, 1.739)
CLASS=HTTP	TCP_PORT_S=80 LOG_DATA_PACK_S=1-2 WIN_MIN_S=2*4k-4*4K => CLASS=HTTP	(13.800%, 100%, 1.739)
CLASS=HTTP	P_REORDERING=0-0.1 LOG_PACK_S=1-2 TCP_PORT_S=80 WIN_MIN_C=8*4k-16*4K LOG_BYTES_C=2-3 => CLASS=HTTP	(11.200%, 100%, 1.739)
CLASS=HTTP	LOG_PACK_S=1-2 LOG_PACK_C=1-2 TCP_PORT_S=80 LOG_DATA_PACK_S=1-2 WIN_MIN_S=2*4k-4*4K => CLASS=HTTP	(11.000%, 100%, 1.739)
CLASS=HTTP	P_REORDERING=0-0.1 TCP_PORT_S=80 WINDOW_SCALE_C=4 => CLASS=HTTP	(10.900%, 100%, 1.739)
CLASS=HTTP	P_REORDERING=0-0.1 LOG_PACK_S=1-2 TCP_PORT_S=80 LOG_DATA_PACK_S=1-2 WIN_MIN_S=2*4k-4*4K => CLASS=HTTP	(13.300%, 100%, 1.739)
CLASS=HTTP	P_REORDERING=0-0.1 LOG_DATA_PACK_C=<1 LOG_PACK_C=1-2 TCP_PORT_S=80 P_DUPLICATE=0-0.1 LOG_BYTES_C=3-4 => CLASS=HTTP	(12.200%, 100%, 1.739)
CLASS=HTTP	P_REORDERING=0-0.1 LOG_PACK_S=1-2 TCP_PORT_S=80 WIN_MIN_S=2*4k-4*4K WINDOW_SCALE_S=2 => CLASS=HTTP	(12.500%, 100%, 1.739)
````
