"""
Test element "is_focused" functionality.
"""
from __future__ import absolute_import

from bok_choy.web_app_test import WebAppTest
from .pages import FocusedPage


class FocusedTest(WebAppTest):
    """
    Test query `is_focused` method and `focused` property.
    """
    def setUp(self):
        super(FocusedTest, self).setUp()
        self.page = FocusedPage(self.browser).visit()

    def test_focused(self):
        self.assertFalse(self.page.q(css="#nonexistent").focused)
        self.assertFalse(self.page.q(css="#main-content").focused)
        self.page.focus_on_main_content()
        self.page.wait_for(
            self.page.q(css="#main-content").is_focused,
            "main content should be focused"
        )
