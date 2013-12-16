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

    @property
    def page_object_classes(self):
        return [SelectorPage]

    def test_count(self):
        self.ui.visit('selector')
        assert_equal(self.ui['selector'].num_divs, 4)

    def test_text(self):
        self.ui.visit('selector')
        assert_equal(
            self.ui['selector'].div_text_list,
            ['Test div 1', 'Test div 2', 'Test div 3', 'Test div 4']
        )

    def test_value(self):
        self.ui.visit('selector')
        assert_equal(
            self.ui['selector'].div_value_list,
            ['value 1', 'value 2', 'value 3', 'value 4']
        )

    def test_html(self):
        self.ui.visit('selector')
        assert_equal(
            self.ui['selector'].div_html_list,
            ['Test div 1', 'Test div 2', 'Test div 3', 'Test div 4']
        )

    def test_is_present(self):
        self.ui.visit('selector')
        assert_true(self.ui['selector'].is_css_present('div#fixture'))
        assert_false(self.ui['selector'].is_css_present('div#not_present'))
