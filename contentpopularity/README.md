# Content Popularity Components

This folder contains various components developed by the mPlane 
project against the mPlane SDK for the use case Estimating Content 
Popularity.

The code for the Python3 mPlane protocol Reference Implementation (RI) is 
available on GitHub under [mPlane protocol RI](https://github.com/fp7mplane/protocol-ri). 

Here we assume that [PROTOCOL_RI_DIR] is the folder where the GitHub 
repository of the mPlane protocol reference implementation has been cloned.


## Reasoner

**cachereasoner** is the Python script for the Reasoner.
It periodically runs the request which returns the
list of contents to cache in a given server.

## Supervisor

The Python code for the supervisor is the one provided 
in the mPlane protocol RI repository, i.e., **scripts/mpsup**.

It receives the requests from the Reasoner and forwards them to the 
repository and analysis module component.

## Repository and Analysis Module

**cacheController.py** is the Python script that returns the list of 
contents to cache.

**tstatrepository.py** integrates the script above with the capabilities
of communicating with Tstat's proxy.

## Howto

Follow these steps:

1. Set the parameters in the files **supervisor.conf**, **cacheController.conf**, **reasoner.conf** (e.g., path to certificates, supervisor address, client port and address, and roles)

2. Set the following parameters in the files **cacheController.py** and **tstatrepository.py** to connect to the Analysis module that estimates the content popularity of contents

        _controller_address = Content Estimation analysis module IP address
        _controller_port = Content Estimation analysis module port
        
        
        
        
3. Run the supervisor

        $ export PYTHONPATH=[PROTOCOL_RI_DIR]
        $ python3 scripts/mpsup --config supervisor.conf

4. Run the cache controller (make sure you have set the MPLANE_RI variable)

        $ export PYTHONPATH=[PROTOCOL_RI_DIR]
        $ python3 cacheController.py --config cacheController.conf 

5. Run the Reasoner (make sure you have set the MPLANE_RI variable)

        $ export PYTHONPATH=[PROTOCOL_RI_DIR]
        $ python3 cachereasoner --config reasoner.conf
