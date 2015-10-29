mPlane Protocol Software Development Kit
========================================

This module contains the mPlane Software Development Kit.

The draft protocol specification is available in
`doc/protocol-spec.md <https://github.com/fp7mplane/protocol-ri/blob/sdk/doc>`__.

The mPlane Protocol provides control and data interchange for passive
and active network measurement tasks. It is built around a simple
workflow in which **Capabilities** are published by **Components**,
which can accept **Specifications** for measurements based on these
Capabilities, and provide **Results**, either inline or via an indirect
export mechanism negotiated using the protocol.

Measurement statements are fundamentally based on schemas divided into
Parameters, representing information required to run a measurement or
query; and Result Columns, the information produced by the measurement
or query. Measurement interoperability is provided at the element level;
that is, measurements containing the same Parameters and Result Columns
are considered to be of the same type and therefore comparable.


Learning More
-------------

See `doc/HOWTO.md <https://github.com/fp7mplane/protocol-ri/blob/sdk/doc/HOWTO-component.md>` for information on getting started with the mPlane SDK for demonstration purposes.

See `doc/conf.md <https://github.com/fp7mplane/protocol-ri/blob/sdk/doc/conf.md>` for an introduction to the mPlane SDK configuration file format.

See `doc/client-shell.md <https://github.com/fp7mplane/protocol-ri/blob/sdk/doc/client-shell.md>` for an introduction to `mpcli` debug client shell.

See `doc/component-dev.md <https://github.com/fp7mplane/protocol-ri/blob/sdk/doc/component-dev.md>` for an introduction to developing components with the mPlane SDK and running them with the `mpcom` runtime.

See `doc/protocol-spec.md <https://github.com/fp7mplane/protocol-ri/blob/sdk/doc/protocol-spec.md>` for the mPlane protocol specification.

Using the mPlane SDK
====================

Prerequisites
-------------

The mPlane SDK requires Python 3.3 and the following additional
packages:

-  pyyaml
-  tornado
-  urllib3

Contents
--------

The SDK is made up of several modules. The core classes are documented
using Sphinx. Reasonably current Sphinx documentation can be read online
`here <https://fp7mplane.github.io/protocol-ri>`__.

-  ``mplane.model``: Information model and JSON representation of mPlane
   messages.
-  ``mplane.scheduler``: Component specification scheduler. Maps
   capabilities to Python code that implements them (in ``Service``) and
   keeps track of running specifications and associated results (``Job``
   and ``MultiJob``).
-  ``mplane.tls``: Handles TLS, mapping local and peer certificates to
   identities and providing TLS connectivity over HTTPS.
-  ``mplane.azn``: Handles access control, mapping identities to roles
   and authorizing roles to use specific services.
-  ``mplane.client``: mPlane client framework. Handles client-initiated
   (``HttpClient``) and component-initiated (``ListenerHttpClient``)
   workflows.

There are two scripts installed with the package, as well:

-  ``mpcli``: Simple client with command-line shell for debugging.
-  ``mpcom``: mPlane component runtime. Handles client-initiated and
   component-initiated workflows.

mPlane SDK Configuration Files
------------------------------

The TLS state, access control, client framework, command-line client,
and component runtime use a unified configuration file in Windows INI
file format (as supported by the Python standard library
``configparser`` module).

The following sections and keys are supported/required by each module:

-  ``TLS`` section: Certificate configuration. Required by component and
   client to support HTTPS URLs. Has the following keys:

   -  ``ca-chain``: path to file containing PEM-encoded certificates for
      the valid certificate authorities.
   -  ``cert``: path to file containing decoded and PEM-encoded
      certificate identifying this component/client. Must contain the
      decoded certificate as well, from which the distinguished name can
      be extracted.
   -  ``key``: path to file containing (decrypted) PEM-encoded secret
      key associated with this component/client's certificate

-  ``Roles`` section: Maps identities to roles for access control. Used
   by component.py. Each key in this section is an mPlane identity (see
   below), and the value is a comma-separated list of arbitrary role
   names assigned to the identity.
-  ``Authorizations`` section: Authorizes defined roles to invoke
   services associated with capabilities by capability label or token.
   Each key is a capability label or token, and the value is a
   comma-separated list of arbitrary role names which may invoke the
   capability. The use of labels is recommended for authorizations, as
   it makes authorization configuration more auditable. If
   authorizations are present, *only* those capabilities which are
   explicitly authorized to a given client identity will be invocable.
-  ``Component`` section: Global configuration for the component
   framework.
-  ``Client`` section: Global configuration for the client framework.
-  ``ClientShell`` section: Contains defaults for the mPlane client
   shell (see mPlane Client Shell below for details).

Component Modules
~~~~~~~~~~~~~~~~~

In addition, any section in a configuration file given to component.py
which begins with the substring ``module_`` will cause a component
module to be loaded at runtime and that modules services to be made
available (see Implementing a Component below). The ``module`` key in
this section identifies the Python module to load by name. All other
keys in this section are passed to the module's ``services()`` function
as keyword arguments.

Identities
~~~~~~~~~~

Identities in the mPlane SDK (for purposes of configuration) are
represented as a dot-separated list of elements of the Distinguished
Name appearing in the certificate associated with the identity. So, for
example, a certificate issued to
``DC=ch, DC=ethz, DC=csg, OU=clients, CN=client-33`` would be
represented in the Roles section of a component configuration as
``ch.ethz.csg.clients.client-33``.

Implementing a Component
------------------------

The component runtime provides a framework for building components for
both component-initiated and client-initiated workflows. To implement a
component for use with this framework:

-  Implement each measurement, query, or other action performed by the
   component as a subclass of mplane.scheduler.Service. Each service is
   bound to a single capability. Your service must implement at least
   the mplane.scheduler.Service.run(self, specification,
   check\_interrupt) method.

-  Implement a ``services`` function in your module that takes a set of
   keyword arguments derived from the configuration file section, and
   returns a list of Services provided by your component. For example:

.. code:: python

    def service(**kwargs):
        return [MyFirstService(kwargs['local-ip-address']),
                MySecondService(kwargs['local-ip-address'])]

-  Create a module section in the component configuration file; for
   example if your module is called mplane.components.mycomponent:

::

    [service_mycomponent]
    module: mplane.components.mycomponent
    local-ip-address: 10.2.3.4

**[*Editor's Note:* need to define how to configure component.py for
each workflow.]**

-  Run ``mpcom`` to start your component. The ``--config`` argument
   points to the configuration file to use.

mPlane Client Shell
-------------------

The mPlane Client Shell is a simple client intended for debugging of
mPlane infrastructures. To start it, simply run ``mpcli``. It supports
the following commands:

-  ``seturl``: Set the default URL for sending specifications and
   redemptions (when not given in a Capability's or Receipt's link
   section)
-  ``getcap``: Retrieve capabilities and withdrawals from a given URL,
   and process them.
-  ``listcap``: List available capabilities
-  ``showcap``: Show the details of a capability given its label or
   token
-  ``when``: Set the temporal scope for a subsequent ``runcap`` command
-  ``set``: Set a default parameter value for a subsequent ``runcap``
   command
-  ``unset``: Unset a previously set default parameter value
-  ``show``: Show a previously set default parameter value
-  ``runcap``: Run a capability given its label or token
-  ``listmeas``: List known measurements (receipts and results)
-  ``showmeas``: Show the details of a measurement given its label or
   token.
-  ``tbenable``: Enable tracebacks for subsequent exceptions. Used for
   client debugging.

Testing and Developing the SDK
==============================

Testing
-------

Unit testing is done with the nose package. To run:

``nosetests --with-doctest mplane.model``

Documentation
-------------

API documentation on
`github <https://fp7mplane.github.io/protocol-ri>`__ is autogenerated
from Python docstrings with sphinx. Regenerating the documentation
requires the sphinx package; once this is installed, use the following
command from the sphinx directory to rebuild the documentation.

``PYTHONPATH=.. make html``
