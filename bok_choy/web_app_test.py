"""
Base class for testing a web application.
"""
from abc import ABCMeta
import functools
import os
import sys
from unittest import SkipTest
from uuid import uuid4

from needle.cases import NeedleTestCase, import_from_string
from selenium.webdriver.support.events import EventFiringWebDriver

from .browser import browser, save_screenshot, save_driver_logs
from .proxy import bmp_proxy, stop_server
from .performance import HarListener, HarCapturer


class WebAppTest(NeedleTestCase):

    """
    Base class for testing a web application.
    """

    __metaclass__ = ABCMeta

    # Execute tests in parallel!
    _multiprocess_can_split_ = True

    def __init__(self, *args, **kwargs):
        super(WebAppTest, self).__init__(*args, **kwargs)

        # This allows using the @attr() decorator from nose to set these on a
        # test by test basis
        self.proxy = getattr(self, 'proxy', None)
        self.har_mode = getattr(
            self, 'har_mode', os.environ.get('BOK_CHOY_HAR_MODE', None))

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

        self.driver.set_window_size(width + delta, height)

    def setUp(self):
        """
        Start the browser for use by the test.
        You *must* call this in the `setUp` method of any subclasses before using the browser!

        Returns:
            None
        """
        super(WebAppTest, self).setUp()

        if self.har_mode:
            # Set up proxy using browsermobproxy if we want to capture har files
            # or if the user has specified that it wants to use browsermobproxy
            self.proxy, server = bmp_proxy()
            self.addCleanup(stop_server, server)

        # Set up the browser
        # This will start the browser
        # If using SauceLabs, tag the job with test info
        tags = [self.id()]
        self.browser = browser(tags, self.proxy)

        # Needle uses these attributes for taking the screenshots
        self.driver = self.get_web_driver()
        self.driver.set_window_position(0, 0)
        self.set_viewport_size(self.viewport_width, self.viewport_height)

        if self.har_mode:
            # Initialize a HarCapturer. The har_capturer instance will always be
            # able to be explicitly interacted with in the test in addition to
            # being accessible to the HarListener for automatic capture.
            self.har_capturer = HarCapturer(
                self.proxy,
                har_base_name=self.id(),
                mode=self.har_mode,
            )

            # In order to automatically capture the har, we need a listener that can
            # track the pages visted. To do this, we can use an
            # EventFiringWebdriver.
            self.browser = EventFiringWebDriver(
                self.browser, HarListener(self.har_capturer))

        # Cleanups are executed in LIFO order.
        # This ensures that the screenshot is taken and the driver logs are saved
        # BEFORE the browser quits.
        self.addCleanup(self.browser.quit)
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
        selenium driver logs, and the captured har file.
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
                save_driver_logs(self.browser, self.id())
            except:  # pylint: disable=bare-except
                pass

            try:
                self.har_capturer.save_har(
                    self.browser,
                    caller_mode=self.har_mode
                )
            except:  # pylint: disable=bare-except
                pass


def with_cache(function):
    """
    A decorator to be used on a test case of a WebAppTest test to run the test twice in
    the same browser instance, capturing a har file each time.

    The first har captured will reflect the performance when there have not been any
    assets cached. The second will reflect the performance of a second visit, having
    possibly cached some assets in the first visit.

    Note that this will only work in 'explicit' and 'auto' modes. Using with `BOK_CHOY_HAR_MODE`
    set to 'error' will only save if the test fails or errors.

    Args:
        function (callable): The function to decorate. It should be a test_case ina a
        WebAppTest instance.

    Returns:
        Decorated method
    """

    @functools.wraps(function)
    def wrapper(self, *args, **kwargs):
        """
        Runs the test case twice. The first time, there will be an empty cache. The second
        time, the cache will contain anything stored on the first call.
        """
        # Run once in a new browser instance.
        function(self, *args, **kwargs)

        self.har_capturer.save_har(self.browser, caller_mode=self.har_mode)
        self.har_capturer._with_cache = True  # pylint: disable=protected-access
        # Run the whole thing again in the same browser instance.
        function(self, *args, **kwargs)

    return wrapper
