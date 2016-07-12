"""
Test JavaScript synchronization.
"""
from __future__ import absolute_import

from bok_choy.promise import BrokenPromise
from bok_choy.web_app_test import WebAppTest
from .pages import JavaScriptPage, RequireJSPage, JavaScriptUndefinedPage


class JavaScriptTest(WebAppTest):
    """
    Test JavaScript synchronization.
    """

    def test_wait_for_defined(self):
        javascript = JavaScriptPage(self.browser)
        javascript.visit()
        javascript.trigger_output()
        assert javascript.output == "Done"

    def test_wait_for_defined_with_reload(self):
        javascript = JavaScriptPage(self.browser)
        javascript.visit()
        javascript.reload_and_trigger_output()
        assert javascript.output == "Done"

    def test_wait_for_defined_failure(self):
        with self.assertRaises(BrokenPromise):
            javascript = JavaScriptUndefinedPage(self.browser)
            javascript.visit()
            javascript.trigger_output()

    def test_wait_for_requirejs(self):
        requirejs = RequireJSPage(self.browser)
        requirejs.visit()
        assert requirejs.output == "Done"
