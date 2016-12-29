#!/usr/bin/env python

import codecs
from setuptools import setup

VERSION = '0.6.1'
DESCRIPTION = 'UI-level acceptance test framework'

# Version for selenium added since needle has a max version which is lower than the current default. If needle ever
# revs to a higher version (currently needle is 0.3) we should remove this.
REQUIREMENTS = (
    'lazy',
    'needle',
    'selenium>=2,<3',
    'six',
)

with codecs.open('README.rst', 'r', 'utf-8') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name='bok_choy',
    version=VERSION,
    author='edX',
    author_email='oscm@edx.org',
    url='http://github.com/edx/bok-choy',
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    license='Apache 2.0',
    classifiers=['Development Status :: 4 - Beta',
                 'Environment :: Console',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: Apache Software License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: Implementation :: CPython',
                 'Programming Language :: Python :: Implementation :: PyPy',
                 'Topic :: Software Development :: Testing',
                 'Topic :: Software Development :: Quality Assurance'],
    packages=['bok_choy', 'bok_choy/a11y'],
    package_data={'bok_choy': ['vendor/google/*.*', 'vendor/axe-core/*.*']},
    install_requires=REQUIREMENTS,
)
