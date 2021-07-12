#! /usr/bin/env python3

import imp
import os
import sys
from setuptools import find_packages, setup
import subprocess

NAME = 'OASYS1-COMSYL'
VERSION = '1.0.17'
ISRELEASED = False

DESCRIPTION = 'oasys-comsyl: Oasys widgets for COMSYL'
README_FILE = os.path.join(os.path.dirname(__file__), 'README.txt')
LONG_DESCRIPTION = open(README_FILE).read()
AUTHOR = 'M. Sanchez del Rio, M. Glass'
AUTHOR_EMAIL = 'srio@esrf.eu'
URL = 'https://github.com/oasys-kit/oasys-comsyl'
DOWNLOAD_URL = 'https://github.com/oasys-kit/oasys-comsyl'
LICENSE = 'MIT'

KEYWORDS = (
    'application',
    'COMSYL',
    'Oasys',
    'Orange',
    'comsyl>=1.0.13',
    )

CLASSIFIERS = (
    'Development Status :: 4 - Beta',
    'Environment :: X11 Applications :: Qt',
    'Environment :: Console',
    'Environment :: Plugins',
    'Programming Language :: Cython',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Intended Audience :: Science/Research',
    )


SETUP_REQUIRES = (
                  'setuptools',
                  )

INSTALL_REQUIRES = (
                    'oasys1>=1.2.10',
                    'comsyl'
                    )

PACKAGES = find_packages(exclude=('*.tests', '*.tests.*', 'tests.*', 'tests'))



PACKAGE_DATA = {
    "":["icons/*.png", "icons/*.jpg"],
    # "orangecontrib.comsyl.widgets.applications":["icons/*.png", "icons/*.jpg"],
    # "orangecontrib.comsyl.widgets.tools":["icons/*.png", "icons/*.jpg"],
    }

NAMESPACE_PACAKGES = ["orangecontrib","orangecontrib.comsyl", "orangecontrib.comsyl.widgets"]


ENTRY_POINTS = {
    'oasys.addons' : ("COMSYL = orangecontrib.comsyl", ),
    'oasys.widgets' : (
            "COMSYL Apps = orangecontrib.comsyl.widgets.applications",
            "COMSYL Tools = orangecontrib.comsyl.widgets.tools",
            ),
    }

if __name__ == '__main__':
    setup(
          name = NAME,
          version = VERSION,
          description = DESCRIPTION,
          long_description = LONG_DESCRIPTION,
          author = AUTHOR,
          author_email = AUTHOR_EMAIL,
          url = URL,
          download_url = DOWNLOAD_URL,
          license = LICENSE,
          keywords = KEYWORDS,
          classifiers = CLASSIFIERS,
          packages = PACKAGES,
          package_data = PACKAGE_DATA,
          setup_requires = SETUP_REQUIRES,
          install_requires = INSTALL_REQUIRES,
          entry_points = ENTRY_POINTS,
          namespace_packages=NAMESPACE_PACAKGES,
          include_package_data = True,
          zip_safe = False,
          )
