"""
Tests for retrieving values from the page using CSS selectors.
"""

from bok_choy.web_app_test import WebAppTest
from .pages import SelectorPage


class SelectorTest(WebAppTest):
    """
    Test retrieving values by CSS selector.
    """

    def setUp(self):
        super(SelectorTest, self).setUp()

        self.selector = SelectorPage(self.browser)
        self.selector.visit()

    def test_count(self):
        self.assertEquals(self.selector.num_divs, 4)

    def test_text(self):
        self.assertEquals(
            self.selector.div_text_list,
            ['Test div 1', 'Test div 2', 'Test div 3', 'Test div 4']
        )

    def test_value(self):
        self.assertEquals(
            self.selector.div_value_list,
            ['value 1', 'value 2', 'value 3', 'value 4']
        )

    def test_html(self):
        self.assertEquals(
            self.selector.div_html_list,
            ['Test div 1', 'Test div 2', 'Test div 3', 'Test div 4']
        )

    def test_is_present(self):
        self.assertTrue(self.selector.is_css_present('div#fixture'))
        self.assertFalse(self.selector.is_css_present('div#not_present'))
