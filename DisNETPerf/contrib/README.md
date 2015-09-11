RIPE Atlas Toolbox
=====================

Atlas Toolbox is a collection of Perl command-line scripts from managing custom User Defined Measurements (UDMs) on the **RIPE Atlas** network.

Atlas is a large measurement network composed of geographically distributed probes used to measure Internet connectivity and reachability.

This toolbox allows to search probes on the network, visualize public measurements set by other Atlas users, configure custom active measurements and get their results. The scripts use Atlas' REST APIs. Currently, the measurement types supported are: **ping**, **traceroute** and **dns**. Other types (e.g. **sslcert** and **http**) will be implemented in future.

Please be aware that **THIS IS A BETA VERSION, MAY CONTAIN SOME BUGS** and does not implement all Atlas' features.

#### List of scripts

- **probe-list**: search probes on the network
- **udm-create**: set up a custom measurement (ping/traceroute/dns)
- **udm-status**: check status of a measurement
- **udm-result**: retrieve results of a measurement
- **udm-stop**: stop a running measurement
- **udm-lookup**: search existing measurements

----------

Prerequisites
-------------

To run the scripts, the Perl interpreter is needed (it comes pre-installed on most systems). 
Additional PERL modules are used, such as HTTP::Request, HTTP::Response, LWP::UserAgent, LWP::Simple, LWP::Protocol::https, JSON and Geo::Coder.

The last three might need to be manually installed via the OS packet manager or CPAN, as showed below.

#### Debian/Ubuntu systems

```sh
sudo apt-get install libjson-perl libgeo-coder-googlev3-perl
```

All other required modules should be already installed in Ubuntu (tested 14.04).

#### Using CPAN (multi-platform)

```sh
sudo perl -MCPAN -e shell
install JSON
install Geo::Coder::Googlev3
install LWP::Protocol::https
```

Check here how to install Perl modules: <http://www.cpan.org/modules/INSTALL.html>

Install
-------

```sh
git clone https://github.com/pierdom/atlas-toolbox
cd atlas-toolbox
```


Usage Examples
--------------

### Find probes

Find at most 5 probes in a specific Autonomous System:
```sh
./probe-list.pl --asn 1234 --limit 5
```
Find all probes in Italy at less than 2Km from an address:
```sh
./probe-list.pl --country it --address "Piazza di Spagna, Rome" --radius 2
```

### Set-up measurements

In order to set-up a UDM, you should first create an API key with 'Measurement creation' permissions.
udm-create.pl will return the measurement ID (UDM-ID) if it is successful or an error code.

Instrument 2 probes to ping a host:
```sh
./udm-create.pl --api <API-KEY> --type ping --target www.example.com --probe-list 1234,5678
```

Resolve a host with probes' default DNS server:
```sh
./udm-create.pl --api <API-KEY> --type dns --dns-arg www.example.com --probe-list 1234,5678
```

Ping a host every 5 minutes for 2 consecutive days and resolve it using probes' default DNS server:
```sh
./udm-create.pl --api <API-KEY> --type ping --target www.example.com --probe-list 1234,5678 --resolve-on-probe --start 1403042400 --stop 1403215199 --interval 300
```

Use probe-list.pl output to define set of probes for a measurement using pipe:
```sh
./probe-list.pl --country it --asd 1234 | ./udm-create.pl --api <API-KEY> --type ping --target example.com
```

### Measurement management (check status, get results and stop)

For measurement management, the UDM-ID is used. In some cases (e.g. private measurement), an API key may be needed (use --api argument).

Print UDM status:
```sh
./udm-status.pl --udm <UDM-ID>
```
Get UDM results:
```sh
./udm-result.pl --udm <UDM-ID>
```
Stop a measurement (requires API key with stop permission):
```sh
./udm-stop.pl --udm <UDM-ID> --api <KEY>
```

### Search existing measurements

Running your own measurement consume credits. It could be that some other user set already up a UDM you are interested. To search an existing measurement:

```sh
./probe-lookup.pl --type traceroute --target www.example.com
```


Documentation
-------------

Every script comes with its own documentation. To see a full list of available arguments, use --help. Example:
```sh
./probe-list.pl --help
```

To read the full documentation:
```sh
perldoc probe-list.pl
```


License
-------

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>


Acknowledgement
---------------

This work has been partially funded by the European Commission 
funded mPlane ICT-318627 project (www.ict-mplane.eu).


Author
------

* Main author: **Pierdomenico Fiadino** - <fiadino@ftw.at> - <http://userver.ftw.at/~fiadino>
* Contributor: **Sarah Wassermann** -  <https://github.com/SAWassermann>
