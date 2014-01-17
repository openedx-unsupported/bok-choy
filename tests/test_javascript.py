"""
Test JavaScript synchronization.
"""

from bok_choy.web_app_test import WebAppTest
from .pages import JavaScriptPage, RequireJSPage


class JavaScriptTest(WebAppTest):
    """
    Test JavaScript synchronization.
    """

    def test_wait_for_defined(self):
        javascript = JavaScriptPage(self.browser)
        javascript.visit()
        javascript.trigger_output()
        self.assertEquals(javascript.output, "Done")

    def test_wait_for_defined_with_reload(self):
        javascript = JavaScriptPage(self.browser)
        javascript.visit()
        javascript.reload_and_trigger_output()
        self.assertEquals(javascript.output, "Done")

    def test_wait_for_requirejs(self):
        requirejs = RequireJSPage(self.browser)
        requirejs.visit()
        self.assertEquals(requirejs.output, "Done")
