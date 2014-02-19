#!/usr/bin/env python

from setuptools import setup

VERSION = '0.3.0'
DESCRIPTION = 'UI-level acceptance test framework'
REQUIREMENTS = [
    line.strip() for line in open("requirements.txt").readlines()
]

setup(
    name='bok_choy',
    version=VERSION,
    author='edX',
    url='http://github.com/edx/bok-choy',
    description=DESCRIPTION,
    license='AGPL',
    classifiers=['Development Status :: 3 - Alpha',
                 'Environment :: Console',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: GNU Affero General Public License v3',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Software Development :: Testing',
                 'Topic :: Software Development :: Quality Assurance'],
    packages=['bok_choy'],
    install_requires=REQUIREMENTS,
)
