"""
Test waiting for elements to appear after a delay.
"""

from bok_choy.web_app_test import WebAppTest
from bok_choy.promise import BrokenPromise
from .pages import DelayPage, SlowPage


class DelayTest(WebAppTest):
    """
    Test waiting for elements to appear after a delay.
    """
    def setUp(self):
        super(DelayTest, self).setUp()
        self.delay = DelayPage(self.browser)
        self.delay.visit()

    def test_delay(self):
        """
        Test retrieving a value from the DOM that does not appear
        until after a delay.
        """
        self.delay.trigger_output()
        assert self.delay.output == "Done"

    def test_broken_promise(self):
        broken_promise_raised = False
        try:
            self.delay.make_broken_promise()
        except BrokenPromise:
            broken_promise_raised = True

        self.assertTrue(broken_promise_raised)


class SlowTest(WebAppTest):
    """
    Test visiting a page that loads its elements into the DOM slowly.
    """
    def setUp(self):
        super(SlowTest, self).setUp()
        self.slow = SlowPage(self.browser)

    def test_slow(self):
        self.slow.visit()
