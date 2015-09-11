.. mPlane Protocol RI documentation master file, created by
   sphinx-quickstart on Wed Dec 18 18:41:43 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

mPlane Software Development Kit for Python 3
============================================

.. automodule:: mplane
   :members:

module mplane.model
-------------------
.. automodule:: mplane.model
   :members:

module mplane.scheduler
-------------------
.. automodule:: mplane.scheduler
   :members:

module mplane.client
-------------------
.. automodule:: mplane.client
   :members:

module mplane.component
-------------------
.. automodule:: mplane.component
   :members:

`mpcli` command-line client
---------------------------

The mPlane Client Shell is a simple client intended for debugging of mPlane infrastructures. To start it, simply run ``mpcli``. It supports the following commands:

- ``seturl``: Set the default URL for sending specifications and redemptions (when not given in a Capability's or Receipt's link section)
- ``getcap``: Retrieve capabilities and withdrawals from a given URL, and process them.
- ``listcap``: List available capabilities
- ``showcap``: Show the details of a capability given its label or token
- ``when``: Set the temporal scope for a subsequent `runcap` command
- ``set``: Set a default parameter value for a subsequent `runcap` command
- ``unset``: Unset a previously set default parameter value
- ``show``: Show a previously set default parameter value
- ``runcap``: Run a capability given its label or token
- ``listmeas``: List known measurements (receipts and results)
- ``showmeas``: Show the details of a measurement given its label or token.
- ``tbenable``: Enable tracebacks for subsequent exceptions. Used for client debugging.


`mpcom` component runtime
-------------------------

The component runtime provides a framework for building components for both component-initiated and client-initiated workflows. To implement a component for use with this framework:

- Implement each measurement, query, or other action performed by the component as a subclass of :class:`mplane.scheduler.Service`. Each service is bound to a single capability. Your service must implement at least :func:`mplane.scheduler.Service.run`.

- Implement a ``services`` function in your module that takes a set of keyword arguments derived from the configuration file section, and returns a list of Services provided by your component. For example:

::

  def service(**kwargs):
      return [MyFirstService(kwargs['local-ip-address']),
              MySecondService(kwargs['local-ip-address'])]

- Create a module section in the component configuration file; for example if your module is called ``mplane.components.mycomponent``:

::

  [service_mycomponent]
  module: mplane.components.mycomponent
  local-ip-address: 10.2.3.4

- Run ``mpcom`` to start your component. The ``--config`` argument points to the configuration file to use.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
