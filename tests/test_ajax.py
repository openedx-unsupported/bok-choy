"""
Test waiting for elements to appear after requesting via ajax.
"""

from bok_choy.promise import BrokenPromise
from bok_choy.web_app_test import WebAppTest
from .pages import AjaxPage, AjaxNoJQueryPage


class AjaxTest(WebAppTest):
    """
    Test waiting for an ajax call to return.
    """
    def setUp(self):
        super().setUp()
        self.ajax = AjaxPage(self.browser)
        self.ajax.visit()

    def test_ajax(self):
        """
        Test retrieving a value from the DOM that
        is populated by an ajax call.
        """
        self.ajax.click_button()
        self.ajax.wait_for_ajax()
        assert self.ajax.output == "Loaded via an ajax call."

    def test_ajax_too_slow(self):
        """
        Test that a BrokenPromise is raised when the ajax requests take longer
        than the timeout.
        """
        # Pretend there are ajax requests pending.
        self.ajax.browser.execute_script('jQuery.active=1')

        with self.assertRaises(BrokenPromise) as exc:
            self.ajax.wait_for_ajax(timeout=1)

        self.assertEqual(
            'Promise not satisfied: Finished waiting for ajax requests.',
            str(exc.exception))


class AjaxNoJQueryTest(WebAppTest):
    """
    Test waiting for a ajax on a page where jQuery isn't loaded.
    """
    def setUp(self):
        super().setUp()
        self.ajax = AjaxNoJQueryPage(self.browser)
        self.ajax.visit()

    def test_ajax_with_slow_jquery(self):
        """
        Test that a BrokenPromise is raised when jQuery is not defined on the
        page.
        """
        with self.assertRaises(BrokenPromise) as exc:
            self.ajax.wait_for_ajax(timeout=1)

        self.assertEqual(
            'Promise not satisfied: Finished waiting for ajax requests.',
            str(exc.exception))
