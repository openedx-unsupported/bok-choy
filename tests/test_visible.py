"""
Test element visibility.
"""

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
