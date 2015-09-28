# Content Curation Components

This folder contains various components developed by the mPlane 
project against the mPlane SDK for the use case Passive Content Curation.

The code for the mPlane protocol Reference Implementation (RI) is 
available on GitHub under [mPlane protocol RI](https://github.com/fp7mplane/protocol-ri). 

Here we assume that [PROTOCOL_RI_DIR] is the folder where the GitHub 
repository of the mPlane protocol reference implementation has been cloned.


## Reasoner

**reasoner** is the Python script for the reasoner.
It periodically runs a query which returns the
list of the 100 most popular contents (their URLs) in the last hour.

## Supervisor

The Python code for the supervisor is the one provided 
in the mPlane protocol RI repository, i.e., **scripts/mpsup**.

It receives the requests from the reasoner and forwards them to the 
repository and analysis module component.

## Repository and Analysis Module

**tstatrepository.py** is the mPlane interface for the tstat-repository
implementing the analysis module for the Content Curation use case.

## Howto

Follow these steps:

1. Set the parameters in the file **reasoner.conf** (e.g., path to certificates, supervisor address, client port and address, and roles)

2. Get the supervisor from the reference implementation [mPlane protocol RI](https://github.com/fp7mplane/protocol-ri), and add the capability "repository-top_popular_urls = guest,admin" in [Authorizations] section of the supervisor configuration file (**supervisor.conf**).

3. Run the supervisor:
 
        $ export PYTHONPATH=[PROTOCOL_RI_DIR]
        $ python3 scripts/mpsup --config supervisor.conf

4. Run the tstat-repository

        $ export PYTHONPATH=[PROTOCOL_RI_DIR]
        $ python3 tstatrepository.py --config conf/tstatrepository.conf 

5. Run the Reasoner

        $ export PYTHONPATH=[PROTOCOL_RI_DIR]
        $ python3 reasoner --config reasoner.conf
