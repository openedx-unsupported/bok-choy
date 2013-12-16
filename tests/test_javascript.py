"""
Test JavaScript synchronization.
"""

from bok_choy.web_app_test import WebAppTest
from nose.tools import assert_equal, assert_true
from .pages import JavaScriptPage, RequireJSPage


class JavaScriptTest(WebAppTest):
    """
    Test JavaScript synchronization.
    """

    @property
    def page_object_classes(self):
        return [JavaScriptPage, RequireJSPage]

    def test_wait_for_defined(self):
        self.ui.visit('javascript')
        self.ui['javascript'].trigger_output()
        assert_equal(self.ui['javascript'].output, "Done")

    def test_wait_for_defined_with_reload(self):
        self.ui.visit('javascript')
        self.ui['javascript'].reload_and_trigger_output()
        assert_equal(self.ui['javascript'].output, "Done")

    def test_wait_for_requirejs(self):
        self.ui.visit('requirejs')
        assert_equal(self.ui['requirejs'].output, "Done")
