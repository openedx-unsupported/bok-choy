bok-choy
========

UI-level acceptance test framework.  `Full documentation available on ReadTheDocs`__.

__ http://bok-choy.readthedocs.org/en/latest/


Overview
--------

A Python framework for writing robust Selenium tests.


Installation
------------

As Bok Choy is a Python framework, you first need to install Python.
If you’re running Linux or Mac OS X, you probably already have it installed.
We recommend that you use `pip <http://www.pip-installer.org/>`_ to install your Python
packages:

.. code-block:: bash

   pip install bok_choy


Running Tests
-------------

To run the test suite for bok-choy itself:

* Install Firefox; as of this writing, the current `version 47.0.1 <https://ftp.mozilla.org/pub/firefox/releases/47.0.1/>`_
  works with the latest selenium Python package (2.53.6)
* Install `phantomjs <http://phantomjs.org/download.html>`_
* Create a virtualenv which uses Python 2.7 (or Python 3.5)
* With that virtualenv activated, run ``pip install -r requirements/tox.txt`` to
  install the `tox <http://tox.testrun.org/>`_ testing tool and its
  dependencies
* Run ``tox -e py27`` (or ``tox -e py35``).
* To test and build the documentation, run ``tox -e doc``
* To run an individual test, run ``py.test tests/<test file>::<test class>::<test name>``


License
-------

The code in this repository is licensed under the Apache License, Version 2.0,
unless otherwise noted.

Please see ``LICENSE.txt`` for details.


How to Contribute
-----------------

Contributions are very welcome. The easiest way is to fork this repo, and then
make a pull request from your fork. The first time you make a pull request, you
may be asked to sign a Contributor Agreement.


Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org


Mailing List and IRC Channel
----------------------------

You can discuss this code on the `edx-code Google Group <https://groups.google.com/forum/#!forum/edx-code>`_
or in the **testing** channel on the `Open edX Slack <https://openedx.slack.com>`_.
