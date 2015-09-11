#!/usr/bin/env python3

from distutils.core import setup
from setuptools import find_packages

long_description = '''
This module contains the mPlane Software Development Kit.

The draft protocol specification is available in
https://github.com/fp7mplane/protocol-ri/blob/master/doc/protocol-spec.md.

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
'''

setup(name='mplane-sdk',
      version='0.9.0',
      description='mPlane Software Development Kit for Python 3',
      long_description = long_description,
      author='Brian Trammell',
      author_email='brian@trammell.ch',
      url='http://github.com/fp7mplane/protocol-ri',
      packages=[ "mplane",
                 "mplane.components"],
      package_data={'mplane': ['registry.json']},
      scripts=['scripts/mpcli', 'scripts/mpcom', 'scripts/mpsup'],
      install_requires=['pyyaml', 'tornado', 'urllib3', 'nose'],
      classifiers=["Development Status :: 3 - Alpha",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: "
                   "GNU Lesser General Public License v3 or later (LGPLv3+)",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python :: 3.3",
                   "Topic :: System :: Networking"]
      )
