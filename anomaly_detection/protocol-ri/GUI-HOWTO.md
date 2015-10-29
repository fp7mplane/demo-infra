## Supervisor GUI implementation

### Description

### Installation

Copy `svgui.py`, `svgui_handler.py` to `protocol-ri/mplane`, if they are not there yet.

Copy `svgui.conf` to the `protocol-ri/conf` directory and make the changes for your environment if needed (eg GUI port, authorizations, TLS, etc,).

Copy `guiconf.json` and the `usersettings/` directory to `protocol-ri` and make the changes for your users if needed.

Copy the `www` directory to the root of your web server, so that the the `http://webserver:port/` address be linked to  `www/login.html`.
### HOWTO

To run the supervisor GUI, from the `protocol-ri` directory, run:

```python3.4 -m mplane.svgui --config conf/svgui.conf 2>~/log/svgui.log```

and in another terminal windows start the components:

```scripts/mpcom --config conf/component.conf```

The `component.conf` file attached contains the ping and the ott-probe modules, please feel free to adjust it according to your needs.
(As the svgui is rather verbose, we suggest to redirect standard error to a logfile as shown above, to avoid the diagnostic to mess up with the clientshell interface.)

#### Client shell access

In the first (svgui) terminal window you can access the clientshell functionality, which means you can run capabilities and see the results from the client shell interface as well. 

#### GUI access

The GUI can be accessed through the `gui-port` defined in `svgui.conf`, under the "[gui]" section, default is 8899. Due to the nature of the GUI access we use it without TLS, eg. simply

```http://supervisor_host:8899```

which will bring to the login screen. The user accounts used with the old svgui are still valid, eg.  `user / user123` and can be found in the `guiconf.json` file.

### Changes since the old svgui

Parameter filtering is unified and works for both Capabilities, Receipts and Results.
Some enhancements are under testing, like extended filtering for probe names, start/end times.
