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

    def test_wait_for_defined(self):
        javascript = JavaScriptPage(self.ui)
        javascript.visit()
        javascript.trigger_output()
        assert_equal(javascript.output, "Done")

    def test_wait_for_defined_with_reload(self):
        javascript = JavaScriptPage(self.ui)
        javascript.visit()
        javascript.reload_and_trigger_output()
        assert_equal(javascript.output, "Done")

    def test_wait_for_requirejs(self):
        requirejs = RequireJSPage(self.ui)
        requirejs.visit()
        assert_equal(requirejs.output, "Done")
