#!/usr/bin/env python


import codecs
import os
import re
import sys

from setuptools import setup

VERSION = '2.0.1'
DESCRIPTION = 'UI-level acceptance test framework'


def load_requirements(*requirements_paths):
    """
    Load all requirements from the specified requirements files.

    Requirements will include any constraints from files specified
    with -c in the requirements files.
    Returns a list of requirement strings.
    """
    # UPDATED VIA SEMGREP - if you need to remove/modify this method remove this line and add a comment specifying why.
    # minor update to allow brackets in library names

    requirements = {}
    constraint_files = set()

    # groups "my-package-name<=x.y.z,..." into ("my-package-name", "<=x.y.z,...")
    requirement_line_regex = re.compile(r"([a-zA-Z0-9-_.\[\]]+)([<>=][^#\s]+)?")

    def add_version_constraint_or_raise(current_line, current_requirements, add_if_not_present):
        regex_match = requirement_line_regex.match(current_line)
        if regex_match:
            package = regex_match.group(1)
            version_constraints = regex_match.group(2)
            existing_version_constraints = current_requirements.get(package, None)
            # it's fine to add constraints to an unconstrained package, but raise an error if there are already
            # constraints in place
            if existing_version_constraints and existing_version_constraints != version_constraints:
                raise BaseException(f'Multiple constraint definitions found for {package}:'
                                    f' "{existing_version_constraints}" and "{version_constraints}".'
                                    f'Combine constraints into one location with {package}'
                                    f'{existing_version_constraints},{version_constraints}.')
            if add_if_not_present or package in current_requirements:
                current_requirements[package] = version_constraints

    # process .in files and store the path to any constraint files that are pulled in
    for path in requirements_paths:
        with open(path) as reqs:
            for line in reqs:
                if is_requirement(line):
                    add_version_constraint_or_raise(line, requirements, True)
                if line and line.startswith('-c') and not line.startswith('-c http'):
                    constraint_files.add(os.path.dirname(path) + '/' + line.split('#')[0].replace('-c', '').strip())

    # process constraint files and add any new constraints found to existing requirements
    for constraint_file in constraint_files:
        with open(constraint_file) as reader:
            for line in reader:
                if is_requirement(line):
                    add_version_constraint_or_raise(line, requirements, False)

    # process back into list of pkg><=constraints strings
    constrained_requirements = [f'{pkg}{version or ""}' for (pkg, version) in sorted(requirements.items())]
    return constrained_requirements


def is_requirement(line):
    """
    Return True if the requirement line is a package requirement.

    Returns:
        bool: True if the line is not blank, a comment,
        a URL, or an included file
    """
    # UPDATED VIA SEMGREP - if you need to remove/modify this method remove this line and add a comment specifying why

    return line and line.strip() and not line.startswith(('-r', '#', '-e', 'git+', '-c'))


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
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.8',
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
