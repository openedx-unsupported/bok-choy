"""
Test wait until next page loads.
"""

from nose.tools import assert_raises
from bok_choy.web_app_test import WebAppTest
from bok_choy.web_app_ui import WebAppUIConfigError
from bok_choy.promise import BrokenPromise
from .pages import ButtonPage, NextPage


class NextPageTest(WebAppTest):
    """
    Test wait for next page to load.
    """

    @property
    def page_object_classes(self):
        return [NextPage, ButtonPage]

    def test_wait_for_next_page(self):
        self.ui.visit('next_page')
        self.ui['next_page'].load_next('button', 1)

    def test_no_page_defined(self):
        assert_raises(WebAppUIConfigError, self.ui.wait_for_page, 'not_a_page')

    def test_next_page_does_not_load(self):
        self.ui.visit('button')
        assert_raises(BrokenPromise, self.ui.wait_for_page, 'next_page', timeout=0.1)
