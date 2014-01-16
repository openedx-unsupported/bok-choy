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
        self.alert = AlertPage(self.ui)
        self.alert.visit()

    def test_confirm(self):
        self.alert.confirm()
        self.assertEquals(self.alert.output, "confirmed")

    def test_cancel(self):
        self.alert.cancel()
        self.assertEquals(self.alert.output, "cancelled")

    def test_dismiss(self):
        self.alert.dismiss()
        self.assertEquals(self.alert.output, "Alert closed")
