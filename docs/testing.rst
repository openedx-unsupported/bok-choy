Testing Environment Configuration
=================================

Testing via TravisCI
--------------------

``bok-choy`` can be used along with Travis CI to test changes remotely. One way to accomplish this testing is by using the X Virtual Framebuffer (xvfb) to imitate a display. To use xvfb, you'll start it up via a ``before_script`` section in your ``.travis.yml`` file, like this:

.. code-block:: yaml

    before_script:
      - "export DISPLAY=:99.0"
      - "sh -e /etc/init.d/xvfb start"
      - sleep 3 # give xvfb some time to start

For more details, see this code example_ and the Travis_ docs.

.. _example: https://github.com/edx/xblock-sdk/blob/c7ec2327c0847dc35f57686945490e97e5cd66a5/.travis.yml#L28-L31
.. _Travis: https://docs.travis-ci.com/user/gui-and-headless-browsers/

Testing via tox
---------------

``bok-choy`` can be used along with tox to test against multiple Python virtual environments containing different versions of requirements.

An important detail when using tox in a Travis CI environment: tox passes along only a fixed list of environment variables to each tox-created virtual environment. When using ``bok-choy`` in tox, the DISPLAY environment variable is needed but is not automatically passed-in. The tox.ini file needs to specify the DISPLAY variable like this:

.. code-block:: yaml

    [testenv]
    passenv =
        DISPLAY

For more details, see the tox_ docs.

.. _tox: https://tox.readthedocs.io/en/latest/config.html#confval-passenv=SPACE-SEPARATED-GLOBNAMES
