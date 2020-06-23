"""
Tests for PageObject wait_for* helpers.
"""

from bok_choy.web_app_test import WebAppTest
from .pages import WaitsPage


class WaitHelpersTest(WebAppTest):
    """
    Test waiting for elements to appear after a delay.
    """
    def setUp(self):
        super(WaitHelpersTest, self).setUp()
        self.wait_page = WaitsPage(self.browser)
        self.wait_page.visit()

    def test_element_presence_wait(self):
        self.wait_page.is_button_output_present()

    def test_element_absence_wait(self):
        self.wait_page.is_class_absent()

    def test_element_visibility_wait(self):
        self.wait_page.is_button_output_visible()

    def test_element_invisibility_wait(self):
        self.wait_page.is_spinner_invisible()
