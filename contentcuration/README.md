# Components for the Content Curation Use Case

This folder contains various components developed by the mPlane 
project against the mPlane SDK for the use case Passive Content Curation.

The code for the mPlane protocol Reference Implementation (RI) is 
available on GitHub under [mPlane protocol RI](https://github.com/fp7mplane/protocol-ri). 

Here we assume that [PROTOCOL_RI_DIR] is the folder where the GitHub 
repository of the mPlane protocol reference implementation has been cloned.


## Reasoner

**reasoner** is the Python script for the reasoner.
It periodically runs a query which returns the
list of the 100 most popular URLs contents in the last hour.

## Supervisor

The Python code for the supervisor is the one provided 
in the mPlane protocol RI repository, i.e., **scripts/mpsup**.

It receives the requests from the reasoner and forwards them to the 
repository and analysis module component.

## Repository and Analysis Module

**tstatrepository.py** is the mPlane interface for the tstat-repository
implementing the analysis modules Content Curation use case.

## Howto

Here follow the steps to run the use case:

1. Set the parameters in the files **reasoner.conf** (e.g., path to certificates, supervisor address, client port and address, and roles)

2. Set the envirnoment variable PYTHONPATH to point to [PROTOCOL_RI_DIR]
    `

        $ export PYTHONPATH=[PROTOCOL_RI_DIR]
    `
    
3. Run the supervisor from the reference implementation [mPlane protocol RI](https://github.com/fp7mplane/protocol-ri) (first, add the capability "repository-top_popular_urls = guest,admin" in [Authorizations] section):
    `

        $ export PYTHONPATH=[PROTOCOL_RI_DIR]
        $ python3 scripts/mpsup --config supervisor.conf
    `

5. Run the tstat-repository
    `

        $ export PYTHONPATH=[PROTOCOL_RI_DIR]
        $ python3 tstatrepository.py --config conf/tstatrepository.conf 
    `

6. Run the reasoner
    `
        $ export PYTHONPATH=[PROTOCOL_RI_DIR]
        $ python3 reasoner --config reasoner.conf
    `

