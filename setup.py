#!/usr/bin/env python
from setuptools import setup

setup(
    setup_requires=[
        'pbr>=5.5.1; python_version >= "3.0"',
        'pbr==3.1.1 ; python_version < "3.0"'
    ],
    pbr=True
)
