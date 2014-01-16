"""
Tests for retrieving values from the page using CSS selectors.
"""

from bok_choy.web_app_test import WebAppTest
from nose.tools import assert_equal, assert_true, assert_false
from .pages import SelectorPage


class SelectorTest(WebAppTest):
    """
    Test retrieving values by CSS selector.
    """

    def setUp(self):
        super(SelectorTest, self).setUp()

        self.selector = SelectorPage(self.ui)
        self.selector.visit()

    def test_count(self):
        assert_equal(self.selector.num_divs, 4)

    def test_text(self):
        assert_equal(
            self.selector.div_text_list,
            ['Test div 1', 'Test div 2', 'Test div 3', 'Test div 4']
        )

    def test_value(self):
        assert_equal(
            self.selector.div_value_list,
            ['value 1', 'value 2', 'value 3', 'value 4']
        )

    def test_html(self):
        assert_equal(
            self.selector.div_html_list,
            ['Test div 1', 'Test div 2', 'Test div 3', 'Test div 4']
        )

    def test_is_present(self):
        assert_true(self.selector.is_css_present('div#fixture'))
        assert_false(self.selector.is_css_present('div#not_present'))
