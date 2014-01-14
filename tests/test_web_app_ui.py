"""
Unit tests for WebAppUI.
"""

import os
import tempfile
import shutil
from unittest import TestCase
from nose.tools import assert_true, assert_equal, assert_raises
from bok_choy.web_app_ui import WebAppUI, WebAppUIConfigError, PageLoadError, WrongPageError
from .pages import SitePage, ButtonPage, TextFieldPage


class DuplicatePage(SitePage):
    """
    Create a page with the same name as another page in the test site.
    """
    name = "button"


class UnavailableURLPage(SitePage):
    """
    Create a page that will return a 404, since the test site
    does not serve it.
    """
    name = "unavailable"


class InvalidURLPage(SitePage):
    """
    Create a page that will return a malformed URL.
    """
    name = "invalid"

    def url(self, **kwargs):
        """
        Allow the caller to control the returned URL using `ui.visit()` kwargs.
        """
        return "http://localhost:/invalid"


class WebAppUITest(TestCase):
    """
    Unit tests for WebAppUI.
    """

    def test_wrong_page(self):

        # Create a UI with two pages
        ui = WebAppUI([ButtonPage, TextFieldPage], [])
        self.addCleanup(ui.quit_browser)

        # Go to the button page
        ui.visit('button')

        # Expect an exception
        assert_raises(WrongPageError, ui.__getitem__, 'text_field')

    def test_no_page_object(self):

        # Create a UI with one page
        ui = WebAppUI([ButtonPage], [])
        self.addCleanup(ui.quit_browser)

        # Expect an exception because we are not on the page
        assert_raises(WebAppUIConfigError, ui.__getitem__, 'no_such_page')

    def test_duplicate_page_error(self):
        """
        Check that we get an error when creating a web app UI
        with duplicate page names.
        """
        assert_raises(WebAppUIConfigError, WebAppUI, [ButtonPage, DuplicatePage], [])

    def test_unavailable_url(self):
        """
        Check error handling for unavailable URL.
        """
        ui = WebAppUI([UnavailableURLPage], [])
        self.addCleanup(ui.quit_browser)
        assert_raises(PageLoadError, ui.visit, 'unavailable')

    def test_invalid_url_exception(self):
        ui = WebAppUI([InvalidURLPage], [])
        self.addCleanup(ui.quit_browser)
        assert_raises(PageLoadError, ui.visit, 'invalid')

    def test_validate_url(self):
        """
        Check error handling for malformed url.
        URLs must have a protocol and host; if a port is specified,
        it must use the correct syntax.
        """
        ui = WebAppUI([], [])
        self.addCleanup(ui.quit_browser)

        for url, is_valid in [
            ("", False), ("invalid", False), ("/invalid", False),
            ("http://localhost:/invalid", False), ("://localhost/invalid", False),
            ("http://localhost", True), ("http://localhost/test", True),
            ("http://localhost:8080", True), ("http://localhost:8080/test", True)
        ]:
            assert_equal(ui.validate_url(url), is_valid)

    def test_page_iterator(self):

        # Create a UI with two page objects
        pages = [ButtonPage, TextFieldPage]
        ui = WebAppUI(pages, [])
        self.addCleanup(ui.quit_browser)

        # Check that we can treat it as an iterator
        assert_equal(['button', 'text_field'], [p for p in ui])
        assert_equal(len(pages), len(ui))

    def test_save_screenshot(self):

        # Create a temp directory to save the screenshot to
        tempdir_path = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(tempdir_path))

        # Configure the screenshot directory using an environment variable
        os.environ['SCREENSHOT_DIR'] = tempdir_path

        # Take a screenshot of a page
        ui = WebAppUI([ButtonPage, TextFieldPage], [])
        self.addCleanup(ui.quit_browser)

        ui.visit('button')
        ui.save_screenshot('button_page')

        # Check that the file was created
        expected_file = os.path.join(tempdir_path, 'button_page.png')
        self.assertTrue(os.path.isfile(expected_file))

        # Check that the file is not empty
        self.assertGreater(os.stat(expected_file).st_size, 100)
