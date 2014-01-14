"""
Test handling of alerts.
"""

from bok_choy.web_app_test import WebAppTest
from nose.tools import assert_equal, assert_true
from .pages import AlertPage


class AlertTest(WebAppTest):
    """
    Test handling of alerts.
    """
    page_object_classes = [AlertPage]

    def test_confirm(self):
        self.ui.visit('alert')
        self.ui['alert'].confirm()
        assert_equal(self.ui['alert'].output, "confirmed")

    def test_cancel(self):
        self.ui.visit('alert')
        self.ui['alert'].cancel()
        assert_equal(self.ui['alert'].output, "cancelled")

    def test_dismiss(self):
        self.ui.visit('alert')
        self.ui['alert'].dismiss()
        assert_equal(self.ui['alert'].output, "Alert closed")
