"""
Unit tests for WebAppUI.
"""

import os
import tempfile
import shutil
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
        self.addCleanup(ui.quit_browser)

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
        self.addCleanup(ui.quit_browser)

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
            self.addCleanup(ui.quit_browser)
            ui.visit('unavailable')

        except PageLoadError:
            load_error_raised = True

        assert_true(load_error_raised)

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
