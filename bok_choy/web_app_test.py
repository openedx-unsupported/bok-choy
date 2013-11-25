"""
Base class for testing a web application.
"""
import time
from unittest import TestCase
from abc import ABCMeta, abstractproperty
from uuid import uuid4
from .web_app_ui import WebAppUI


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
        self.ui = WebAppUI(self.page_object_classes, tags)
        self.addCleanup(self.ui.quit_browser)

    @abstractproperty
    def page_object_classes(self):
        """
        Subclasses override this to return a list
        of `PageObject` subclasses to visit
        during the test.
        """
        return []

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
