#!/usr/bin/env python

from setuptools import setup, find_packages
from os import path
import sys

this_directory = path.abspath(path.dirname(__file__))
# NB this fails on python 2.6, but no longer supported
if sys.version_info.major < 3:
    from io import open
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as readme_md:
    long_description = readme_md.read()

develop_require = [
    'pytest', 'pytest-cov',
    'pytest-mock',
]

extras_require = {
    'develop' : develop_require,
}

setup(
    name='itk_pdb',
    version='0.0.2',
    description='Python wrapper to ITk Production DB',
    long_description=long_description,
    url='https://gitlab.cern.ch/atlas-itk/sw/db/production_database_scripts',
    author='Matthew Basso, Jiayi Chen, Bruce Gallop, Giordon Stark',
    author_email='bruce.gallop@cern.ch, gstark@cern.ch',
    include_package_data=True,
    packages=find_packages(".", exclude=["testing"]),
    install_requires=[
        'requests'
    ],
    extras_require=extras_require,
)
