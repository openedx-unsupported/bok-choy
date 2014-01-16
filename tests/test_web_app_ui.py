"""
Unit tests for WebAppUI.
"""

import os
import tempfile
import shutil
from unittest import TestCase
from nose.tools import assert_true, assert_equal, assert_raises
from bok_choy.web_app_ui import WebAppUI, WebAppUIConfigError
from bok_choy.page_object import PageLoadError, WrongPageError
from .pages import SitePage, ButtonPage, TextFieldPage


class UnavailableURLPage(SitePage):
    """
    Create a page that will return a 404, since the test site
    does not serve it.
    """
    name = "unavailable"


class WebAppUITest(TestCase):
    """
    Unit tests for WebAppUI.
    """

    def test_wrong_page(self):

        # Create a UI with two pages
        ui = WebAppUI([])
        self.addCleanup(ui.quit_browser)

        # Go to the button page
        ButtonPage(ui).visit()

        # Expect an exception
        with assert_raises(WrongPageError):
            TextFieldPage(ui).enter_text('foo')

    def test_unavailable_url(self):
        """
        Check error handling for unavailable URL.
        """
        ui = WebAppUI([])
        self.addCleanup(ui.quit_browser)

        with assert_raises(PageLoadError):
            UnavailableURLPage(ui).visit()

    def test_save_screenshot(self):

        # Create a temp directory to save the screenshot to
        tempdir_path = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(tempdir_path))

        # Configure the screenshot directory using an environment variable
        os.environ['SCREENSHOT_DIR'] = tempdir_path

        # Take a screenshot of a page
        ui = WebAppUI([])
        self.addCleanup(ui.quit_browser)

        ButtonPage(ui).visit()
        ui.save_screenshot('button_page')

        # Check that the file was created
        expected_file = os.path.join(tempdir_path, 'button_page.png')
        self.assertTrue(os.path.isfile(expected_file))

        # Check that the file is not empty
        self.assertGreater(os.stat(expected_file).st_size, 100)
