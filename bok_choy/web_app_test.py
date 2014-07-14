"""
Base class for testing a web application.
"""
import sys
from unittest import TestCase
from abc import ABCMeta
from uuid import uuid4
from .browser import browser, save_screenshot


class WebAppTest(TestCase):
    """
    Base class for testing a web application.
    """

    __metaclass__ = ABCMeta

    # Execute tests in parallel!
    _multiprocess_can_split_ = True

    def setUp(self):
        """
        Start the browser for use by the test.
        You *must* call this in the `setUp` method of any subclasses before using the browser!

        Returns:
            None
        """

        # If using SauceLabs, tag the job with test info
        tags = [self.id()]

        # Set up the page objects
        # This will start the browser, so add a cleanup
        self.browser = browser(tags)

        # Cleanups are executed in LIFO order.
        # This ensures that the screenshot is taken BEFORE the browser quits.
        self.addCleanup(self.browser.quit)
        self.addCleanup(self._screenshot)

    @property
    def unique_id(self):
        """
        Helper method to return a uuid.

        Returns:
            39-char UUID string
        """
        return str(uuid4().int)

    def _screenshot(self):
        """
        Take a screenshot on failure or error.
        """
        # Determine whether the test case succeeded or failed
        result = sys.exc_info()

        # If it failed, take a screenshot
        # The exception info will either be an assertion error (on failure)
        # or an actual exception (on error)
        if result != (None, None, None):
            try:
                save_screenshot(self.browser, self.id())
            except:
                pass
