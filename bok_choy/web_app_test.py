"""
Base class for testing a web application.
"""
from __future__ import absolute_import

from abc import ABCMeta
import sys
from unittest import SkipTest
from uuid import uuid4

from needle.cases import NeedleTestCase, import_from_string
from needle.driver import NeedlePhantomJS
import six

from .browser import browser, save_screenshot, save_driver_logs, save_source


@six.add_metaclass(ABCMeta)
class WebAppTest(NeedleTestCase):

    """
    Base class for testing a web application.
    """

    # Execute tests in parallel!
    _multiprocess_can_split_ = True

    def __init__(self, *args, **kwargs):
        super(WebAppTest, self).__init__(*args, **kwargs)

        # This allows using the @attr() decorator from nose to set these on a
        # test by test basis
        self.proxy = getattr(self, 'proxy', None)

    @classmethod
    def setUpClass(cls):
        """
        Override NeedleTestCase's setUpClass method so that it does not
        start up the browser once for each testcase class.
        Instead we start up the browser once per TestCase instance,
        in the setUp method.
        """
        # Instantiate the diff engine.
        # This will allow Needle's flexibility for choosing which you want to use.
        # These lines are copied over from Needle's setUpClass method.
        klass = import_from_string(cls.engine_class)
        cls.engine = klass()

        # Needle's setUpClass method set up the driver (thus starting up the browser),
        # and set the initial window position and viewport size.
        # Those lines are not copied here into WebAppTest's setUpClass method,
        # but instead into our setUp method. This follows our paradigm of starting
        # up a new browser session for each TestCase.

        # Now call the super of the NeedleTestCase class, so that we get everything
        # from the setUpClass method of its parent (unittest.TestCase).
        super(NeedleTestCase, cls).setUpClass()  # pylint: disable=bad-super-call

    @classmethod
    def tearDownClass(cls):
        """
        Override NeedleTestCase's tearDownClass method because it
        would quit the browser. This is not needed as we have already quit the browser
        after each TestCase, by virtue of a cleanup that we add in the setUp method.
        """
        # We still want to call the super of the NeedleTestCase class, so that we get
        # everything from the tearDownClass method of its parent (unittest.TestCase).
        super(NeedleTestCase, cls).tearDownClass()  # pylint: disable=bad-super-call

    def get_web_driver(self):
        """
        Override NeedleTestCases's get_web_driver class method to return the WebDriver instance
        that is already being used, instead of starting up a new one.
        """
        return self.browser

    def quit_browser(self):
        """
        Terminate the web browser which was launched to run the tests.
        """
        if isinstance(self.browser, NeedlePhantomJS):
            # Workaround for https://github.com/SeleniumHQ/selenium/issues/767
            self.browser.service.send_remote_shutdown_command()
            self.browser.service._cookie_temp_file = None  # pylint:disable=protected-access
        self.browser.quit()

    def set_viewport_size(self, width, height):
        """
        Override NeedleTestCases's set_viewport_size class method because we need it to operate
        on the instance not the class.

        See the Needle documentation at http://needle.readthedocs.org/ for information on this
        feature. It is particularly useful to predict the size of the resulting screenshots
        when taking fullscreen captures, or to test responsive sites.
        """
        self.driver.set_window_size(width, height)

        # Measure the difference between the actual document width and the
        # desired viewport width so we can account for scrollbars:
        script = "return {width: document.body.clientWidth, height: document.body.clientHeight};"
        measured = self.driver.execute_script(script)
        delta = width - measured['width']

        if delta > 0:
            self.driver.set_window_size(width + delta, height)

    def setUp(self):
        """
        Start the browser for use by the test.
        You *must* call this in the `setUp` method of any subclasses before using the browser!

        Returns:
            None
        """
        super(WebAppTest, self).setUp()

        # Set up the browser
        # This will start the browser
        # If using SauceLabs, tag the job with test info
        tags = [self.id()]
        self.browser = browser(tags, self.proxy)

        # Needle uses these attributes for taking the screenshots
        self.driver = self.get_web_driver()
        self.driver.set_window_position(0, 0)
        self.set_viewport_size(self.viewport_width, self.viewport_height)

        # Cleanups are executed in LIFO order.
        # This ensures that the screenshot is taken and the driver logs are saved
        # BEFORE the browser quits.
        self.addCleanup(self.quit_browser)
        self.addCleanup(self._save_artifacts)

    @property
    def unique_id(self):
        """
        Helper method to return a uuid.

        Returns:
            39-char UUID string
        """
        return str(uuid4().int)  # pylint: disable=no-member

    def _save_artifacts(self):
        """
        On failure or error save a screenshot, the
        source html, and the selenium driver logs.
        """
        # Determine whether the test case succeeded or failed
        result = sys.exc_info()
        exception_type = result[0]

        # Do not save artifacts for skipped tests.
        if exception_type is SkipTest:
            return

        # If it failed, take a screenshot and save the driver logs.
        # The exception info will either be an assertion error (on failure)
        # or an actual exception (on error)
        if result != (None, None, None):
            try:
                save_screenshot(self.browser, self.id())
            except:  # pylint: disable=bare-except
                pass

            try:
                save_source(self.browser, self.id())
            except:  # pylint: disable=bare-except
                pass

            try:
                save_driver_logs(self.browser, self.id())
            except:  # pylint: disable=bare-except
                pass
