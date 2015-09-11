"""
.. moduleauthor:: Brian Trammell <brian@trammell.ch>

This module provides software development kit for building applications on top of the mPlane protocol. It is organized into serval modules:

:mod:`mplane.model` implements the mPlane protocol information model: message
types, the element registry, and various support classes. On top of the
information model, the :mod:`mplane.scheduler` module defines a framework for
binding :class:`mplane.model.Capability` classes to runnable code, and for
invoking that code on the receipt of mPlane Statements; this is used to build
clients and components.

The :mod:`mplane.client` module defines interfaces for building clients; the    ``mpcli`` script provides a simple command-line interface to this client.

The :mod:`mplane.component` module defines interfaces for building components; the component runtime can be started by running the ``mpcom`` script.

This software is copyright 2013-2015 the mPlane Consortium.
It is made available under the terms of the
`GNU Lesser General Public License <http://www.gnu.org/licenses/lgpl.html>`_,
version 3 or, at your option, any later version.

"""

from . import model
from . import scheduler
