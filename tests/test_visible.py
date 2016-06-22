"""
Test element visibility.
"""
from __future__ import absolute_import

from bok_choy.web_app_test import WebAppTest
from .pages import VisiblePage


class VisibleTest(WebAppTest):
    """
    Test element visibility.
    """
    def setUp(self):
        super(VisibleTest, self).setUp()
        self.page = VisiblePage(self.browser).visit()

    def test_visible(self):
        self.assertTrue(self.page.is_visible('superman'))
        self.assertFalse(self.page.is_visible('batman'))
        self.assertFalse(self.page.is_invisible('superman'))

    def test_visible_with_incorrect_css_selector(self):
        self.assertFalse(self.page.is_visible('sandman'))

    def test_invisible(self):
        self.assertTrue(self.page.is_invisible('joker'))

    def test_not_invisible(self):
        """
        If an element is not present, then it cannot be invisible, either
        """
        self.assertFalse(self.page.is_invisible('foobar'))
