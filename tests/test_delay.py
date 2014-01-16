"""
Test waiting for elements to appear after a delay.
"""

from bok_choy.web_app_test import WebAppTest
from bok_choy.promise import BrokenPromise
from nose.tools import assert_equal, assert_true
from .pages import DelayPage


class DelayTest(WebAppTest):
    """
    Test waiting for elements to appear after a delay.
    """
    def setUp(self):
        super(DelayTest, self).setUp()
        self.delay = DelayPage(self.ui)
        self.delay.visit()

    def test_delay(self):
        """
        Test retrieving a value from the DOM that does not appear
        until after a delay.
        """
        self.delay.trigger_output()
        assert_equal(self.delay.output, "Done")

    def test_broken_promise(self):
        broken_promise_raised = False
        try:
            self.delay.make_broken_promise()
        except BrokenPromise:
            broken_promise_raised = True

        assert_true(broken_promise_raised)
