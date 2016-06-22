Browser Customization
=====================

Although the default browser configurations provided by bok-choy should be
sufficient for most needs, sometimes you'll need to customize it a little
for particular tests or even an entire test suite.  Here are some of the
options bok-choy provides for doing that.

Firefox Profile Preferences
---------------------------

Whether you use a custom profile or not, you can customize the profile's
preferences before the browser is launched.  To do this, create a function
which takes a
`FirefoxProfile <https://seleniumhq.github.io/selenium/docs/api/py/webdriver_firefox/selenium.webdriver.firefox.firefox_profile.html#selenium.webdriver.firefox.firefox_profile.FirefoxProfile>`_
as a parameter and add it via the
``bok_choy.browser.add_profile_customizer()`` function.  For example,
to suppress the "unresponsive script" warning dialog that normally interrupts
a test case in Firefox when running accessibility tests on a particularly long
page:

.. code-block:: python

    def customize_preferences(profile):
        profile.set_preference('dom.max_chrome_script_run_time', 0)
        profile.set_preference('dom.max_script_run_time', 0)
    bok_choy.browser.add_profile_customizer(customize_preferences)

This customization can be done in any of the normal places that test setup
occurs: ``setUpClass()``, a pytest fixture, the test case itself, etc.  You
can clear any previously-added profile customizers via the
``bok_choy.browser.clear_profile_customizers()`` function.

Firefox Profile Directory
-------------------------

Normally, selenium launches Firefox using a new, anonymous user profile.  If
you have a specific Firefox profile that you'd like to use instead, you can
specify the path to its directory in the ``FIREFOX_PROFILE_PATH`` environment
variable anytime before the call to ``bok_choy.browser.browser()``.  This
passes the path to the
`FirefoxProfile constructor <https://seleniumhq.github.io/selenium/docs/api/py/webdriver_firefox/selenium.webdriver.firefox.firefox_profile.html#selenium.webdriver.firefox.firefox_profile.FirefoxProfile>`_
so the browser can be launched with any customizations that have been made to
that profile.
