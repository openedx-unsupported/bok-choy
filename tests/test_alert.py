"""
Test handling of alerts.
"""

from bok_choy.web_app_test import WebAppTest
from .pages import AlertPage


class AlertTest(WebAppTest):
    """
    Test handling of alerts.
    """
    def setUp(self):
        super(AlertTest, self).setUp()
        self.alert = AlertPage(self.browser)
        self.alert.visit()

    def test_confirm(self):
        self.alert.confirm()
        assert self.alert.output == "confirmed"

    def test_cancel(self):
        self.alert.cancel()
        assert self.alert.output == "cancelled"

    def test_dismiss(self):
        self.alert.dismiss()
        assert self.alert.output == "Alert closed"
