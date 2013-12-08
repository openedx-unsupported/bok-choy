"""
Unit tests for WebAppUI.
"""

from unittest import TestCase
from nose.tools import assert_true, assert_equal
from bok_choy.web_app_ui import WebAppUI, WebAppUIConfigError, PageLoadError, WrongPageError
from .pages import SitePage, ButtonPage, TextFieldPage


class DuplicatePage(SitePage):
    """
    Create a page with the same name as another page in the test site.
    """
    NAME = "button"


class InvalidURLPage(SitePage):
    """
    Create a page that will return a 404, since the test site
    does not serve it.
    """
    NAME = "unavailable"


class WebAppUITest(TestCase):
    """
    Unit tests for WebAppUI.
    """

    def test_wrong_page(self):

        # Create a UI with two pages
        ui = WebAppUI([ButtonPage, TextFieldPage], [])

        # Go to the button page
        ui.visit('button')

        # Try using the text field page
        # Expect that an exception gets raised
        wrong_page_raised = False
        try:
            ui['text_field'].enter_text('Lorem ipsum')

        except WrongPageError:
            wrong_page_raised = True

        assert_true(wrong_page_raised)

    def test_no_page_object(self):

        # Create a UI with one page
        ui = WebAppUI([ButtonPage], [])

        # Try accessing a page object that doesn't exist
        config_error_raised = False
        try:
            ui['no_such_page'].is_browser_on_page()

        # Expect that an error is raised
        except WebAppUIConfigError:
            config_error_raised = True

        assert_true(config_error_raised)

    def test_duplicate_page_error(self):
        """
        Check that we get an error when creating a web app UI
        with duplicate page names.
        """

        config_error_raised = False

        try:
            WebAppUI([ButtonPage, DuplicatePage], [])

        except WebAppUIConfigError:
            config_error_raised = True

        assert_true(config_error_raised)

    def test_invalid_url(self):
        """
        Check error handling for unavailable URL.
        """
        load_error_raised = False
        try:
            ui = WebAppUI([InvalidURLPage], [])
            ui.visit('unavailable')

        except PageLoadError:
            load_error_raised = True

        assert_true(load_error_raised)

    def test_page_iterator(self):

        # Create a UI with two page objects
        pages = [ButtonPage, TextFieldPage]
        ui = WebAppUI(pages, [])

        # Check that we can treat it as an iterator
        assert_equal(['button', 'text_field'], [p for p in ui])
        assert_equal(len(pages), len(ui))
