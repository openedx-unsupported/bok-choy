"""
Base class for testing a web application.
"""
import sys
from unittest import TestCase, SkipTest
from abc import ABCMeta
from uuid import uuid4
import functools
import os
from .browser import browser, save_screenshot, save_driver_logs
from .proxy import bmp_proxy, stop_server
from .performance import HarListener, HarCapturer
from selenium.webdriver.support.events import EventFiringWebDriver


class WebAppTest(TestCase):

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

    def setUp(self):
        """
        Start the browser for use by the test.
        You *must* call this in the `setUp` method of any subclasses before using the browser!

        Returns:
            None
        """

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
        return str(uuid4().int)

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
            except:
                pass

            try:
                save_driver_logs(self.browser, self.id())
            except:
                pass

            try:
                self.har_capturer.save_har(
                    self.browser,
                    caller_mode=self.har_mode
                )
            except:
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
        self.har_capturer._with_cache = True
        # Run the whole thing again in the same browser instance.
        function(self, *args, **kwargs)

    return wrapper
