# mPlane Anomaly Detection component proxy and mpAD_Reasoner

This module contains the proxy component to run the Anomaly Detection module and the Reasoner guiding the Anomaly Detection and Diagnosis use case, developed utilizing mPlane SDK.

## Reasoner
The __mpadtoolreasoner__ is a Python script based on __mpcli__ and extended to run reasoning tasks triggered by __adtool.pl__ .

##Supervisor

Supervisor used is the one provided by mPlane SDK.

##Howto

Follow these steps to run the use case.

1. Set parameters for supervisor.conf, adtool.conf, client.conf. NOTE: use the mPlane docs on how to set parameters in configuration files.
2. Run the mPlane Supervisor: open new terminal, enter protocol-ri, and execute:
```
$ export PYTHONPATH=.
$ ./scripts/mpsup --config ./conf/supervisor.conf
```
3. Run adtool component proxy:
Open a new terminal, enter __protocol-ri__ folder and execute:

```
$ export PYTHONPATH=.
$ ./scripts/mpcom --config ./mplane/components/ADTool/conf/adtool.conf

```

4. Run the mpAD_Reasoner:

```
$ export PYTHONPATH=.
$ ./scripts/mpadtoolreasoner --config ./conf/client.conf

```
