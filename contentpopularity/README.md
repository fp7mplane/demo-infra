# Components for the Content Popularity Use Case

This folder contains various components developed by the mPlane 
project against the mPlane SDK for the use case Estimating Content 
Popularity.

The code for the mPlane protocol Reference Implementation (RI) is 
available on GitHub under [mPlane protocol RI](https://github.com/fp7mplane/protocol-ri). 

Here we assume that [PROTOCOL_RI_DIR] is the folder where the GitHub 
repository of the mPlane protocol reference implementation has been cloned.


## Reasoner

**cachereasoner** is the Python script for the reasoner.
It periodically runs the request which returns the
list of contents to cache in a given server.

## Supervisor

The Python code for the supervisor is the one provided 
in the mPlane protocol RI repository, i.e., **scripts/mpsup**.

It receives the requests from the reasoner and forwards them to the 
repository and analysis module component.

## Repository and Analysis Module

**cacheController.py** is the Python script that returns the list of 
contents to cache.

**tstatrepository.py** integrates the script above with the capabilities
of communicating with Tstat.

## Howto

Here follow the steps to run the use case:

1. Set the parameters in the files **supervisor.conf**, **cacheController.conf**, **reasoner.conf** (e.g., path to certificates, supervisor address, client port and address, and roles)

2. Set the envirnoment variable MPLANE_RI to point to [PROTOCOL_RI_DIR]
    `

        $ export MPLANE_RI=[PROTOCOL_RI_DIR]
    `
    
3. Set the following parameters in the files **cacheController.py** and **tstatrepository.py** to connect to the Analysis module that estimates the content popularity of contents
    `

        _controller_address = Content Estimation analysis module address
        _controller_port = Content Estimation analysis module port
    `

4. Run the supervisor
    `
    
        $ python3 scripts/mpsup --config supervisor.conf
    `

5. Run the cache controller (make sure you have set the MPLANE_RI variable)
    `

        $ python3 cacheController.py --config cacheController.conf 
    `

6. Run the reasoner (make sure you have set the MPLANE_RI variable)
    `

        $ python3 cachereasoner --config reasoner.conf
    `

