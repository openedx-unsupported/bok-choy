"""
Test wait until next page loads.
"""

from bok_choy.web_app_test import WebAppTest
from bok_choy.web_app_ui import WebAppUIConfigError
from bok_choy.promise import BrokenPromise
from .pages import ButtonPage, NextPage


class NextPageTest(WebAppTest):
    """
    Test wait for next page to load.
    """

    def setUp(self):
        super(NextPageTest, self).setUp()
        self.next_page = NextPage(self.ui)

    def test_wait_for_next_page(self):
        self.next_page.visit()
        self.next_page.load_next(ButtonPage(self.ui), 1)

    def test_next_page_does_not_load(self):
        ButtonPage(self.ui).visit()
        with self.assertRaises(BrokenPromise):
            self.next_page.wait_for_page(timeout=0.1)
