#!/usr/bin/env python
from __future__ import absolute_import, print_function

import codecs
import os
import sys
from setuptools import setup

VERSION = '0.9.3'
DESCRIPTION = 'UI-level acceptance test framework'


def load_requirements(*requirements_paths):
    """
    Load all requirements from the specified requirements files.
    Returns a list of requirement strings.
    """
    requirements = set()
    for path in requirements_paths:
        requirements.update(
            line.split('#')[0].strip() for line in open(path).readlines()
            if is_requirement(line.strip())
        )
    return list(requirements)


def is_requirement(line):
    """
    Return True if the requirement line is a package requirement;
    that is, it is not blank, a comment, a URL, or an included file.
    """
    return not (
        line == '' or
        line.startswith('-c') or
        line.startswith('-r') or
        line.startswith('#') or
        line.startswith('-e') or
        line.startswith('git+')
    )


if sys.argv[-1] == 'tag':
    print("Tagging the version on github:")
    os.system("git tag -a v%s -m 'v%s'" % (VERSION, VERSION))
    os.system("git push --tags")
    sys.exit()

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
    classifiers=['Development Status :: 5 - Production/Stable',
                 'Environment :: Console',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: Apache Software License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: Implementation :: CPython',
                 'Programming Language :: Python :: Implementation :: PyPy',
                 'Topic :: Software Development :: Testing',
                 'Topic :: Software Development :: Quality Assurance'],
    packages=['bok_choy', 'bok_choy/a11y'],
    package_data={'bok_choy': ['vendor/google/*.*', 'vendor/axe-core/*.*']},
    install_requires=load_requirements('requirements/base.in'),
    extras_require={
        'visual_diff': ['needle']
    }
)
