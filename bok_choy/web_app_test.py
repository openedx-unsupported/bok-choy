"""
Base class for testing a web application.
"""
import sys
import time
from unittest import TestCase
from abc import ABCMeta, abstractproperty
from uuid import uuid4
from .browser import browser, save_screenshot


class TimeoutError(Exception):
    pass


class WebAppTest(TestCase):
    """
    Base class for testing a web application.
    """

    __metaclass__ = ABCMeta

    # Execute tests in parallel!
    _multiprocess_can_split_ = True

    # Subclasses can use this property
    # to access the `WebAppUI` object under test
    ui = None

    def setUp(self):

        # Install fixtures provided by the concrete subclasses
        # By the time this loop exits, all the test pre-conditions
        # should be satisfied.
        for fix in self.fixtures:
            fix.install()

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
    def fixtures(self):
        """
        Return a list of `WebAppFixture` subclasses
        defining the pre-conditions for running the test.

        Fixtures will be installed in the order provided.
        """
        return []

    @property
    def unique_id(self):
        """
        Helper method to return a uuid.
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
