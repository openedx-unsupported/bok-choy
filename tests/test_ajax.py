"""
Test waiting for elements to appear after requesting via ajax.
"""

from bok_choy.web_app_test import WebAppTest
from .pages import AjaxPage


class AjaxTest(WebAppTest):
    """
    Test waiting for an ajax call to return.
    """
    def setUp(self):
        super(AjaxTest, self).setUp()
        self.ajax = AjaxPage(self.browser)
        self.ajax.visit()

    def test_ajax(self):
        """
        Test retrieving a value from the DOM that
        is populated by an ajax call.
        """
        self.ajax.click_button()
        self.ajax.wait_for_ajax()
        self.assertEquals(self.ajax.output, "Loaded via an ajax call.")
