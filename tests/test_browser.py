"""
Tests browser instantiation, selection, etc
"""

import tempfile
import shutil
import os
import socket
from mock import patch
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from unittest import TestCase

import bok_choy.browser
from bok_choy.promise import BrokenPromise
from .pages import ButtonPage, JavaScriptPage


class TestBrowser(TestCase):
    """
    Tests browser functionality (starting browser, choosing browser, etc)
    """

    @patch.dict(os.environ, {'SELENIUM_BROWSER': 'firefox'})
    def test_local_browser(self):
        browser = bok_choy.browser.browser()
        self.addCleanup(browser.quit)
        self.assertIsInstance(browser, webdriver.Firefox)

    @patch.dict(os.environ, {'SELENIUM_BROWSER': 'firefox'})
    def test_firefox_preferences(self):
        browser = bok_choy.browser.browser()
        self.addCleanup(browser.quit)
        # In-spite of the name, 'default_preferences' represents the preferences
        # that are in place on the browser. (The underlying preferences start
        # with default_preferences and are updated in-place.)
        preferences = browser.profile.default_preferences
        self.assertEqual(preferences['browser.startup.homepage'], 'about:blank')
        self.assertEqual(preferences['startup.homepage_welcome_url'], 'about:blank')
        self.assertEqual(preferences['startup.homepage_welcome_url.additional'], 'about:blank')

    @patch.dict(os.environ, {'SELENIUM_BROWSER': 'phantomjs'})
    def test_phantom_browser(self):
        browser = bok_choy.browser.browser()
        self.addCleanup(browser.quit)
        self.assertIsInstance(browser, webdriver.PhantomJS)

    @patch.dict(os.environ, {'SELENIUM_BROWSER': 'invalid'})
    def test_invalid_browser_name(self):
        with self.assertRaises(bok_choy.browser.BrowserConfigError):
            bok_choy.browser.browser()

    @patch.dict(os.environ, {'SELENIUM_FIREFOX_PATH': '/foo/path'})
    def test_custom_firefox_path(self):
        browser_kwargs_tuple = bok_choy.browser._local_browser_class('firefox')
        self.assertTrue('firefox_binary' in browser_kwargs_tuple[2])

    @patch.dict(os.environ, {'SELENIUM_FIREFOX_PATH': ''})
    def test_no_custom_firefox_path(self):
        browser_kwargs_tuple = bok_choy.browser._local_browser_class('firefox')
        self.assertFalse('firefox_binary' in browser_kwargs_tuple[2])

    def test_profile_error(self):
        """
        If there is a WebDriverException when instantiating the driver,
         it should be tried again.
        """
        patcher = patch('bok_choy.browser._local_browser_class')
        patch_object = patcher.start()
        patch_object.side_effect = WebDriverException(msg='oops', screen=None, stacktrace=None)
        self.addCleanup(patch.stopall)
        with self.assertRaises(BrokenPromise):
            bok_choy.browser.browser()
        self.assertEqual(patch_object.call_count, 3)

    @patch.dict(os.environ, {'FIREFOX_PROFILE_PATH': '/foo/path'})
    def test_custom_firefox_profile(self):
        patch_object = patch.object(webdriver, 'FirefoxProfile').start()
        self.addCleanup(patch.stopall)
        browser_kwargs_tuple = bok_choy.browser._local_browser_class('firefox')
        self.assertTrue('firefox_profile' in browser_kwargs_tuple[2])
        patch_object.assert_called_with('/foo/path')

    @patch.dict(os.environ, {'FIREFOX_PROFILE_PATH': ''})
    def test_no_custom_firefox_profile(self):
        patch_object = patch.object(webdriver, 'FirefoxProfile').start()
        self.addCleanup(patch.stopall)
        browser_kwargs_tuple = bok_choy.browser._local_browser_class('firefox')
        self.assertTrue('firefox_profile' in browser_kwargs_tuple[2])
        patch_object.assert_called_with()

    def test_socket_error(self):
        """
        If there is a socket error when instantiating the driver,
         it should be tried again.
        """
        patcher = patch('bok_choy.browser._local_browser_class')
        patch_object = patcher.start()
        patch_object.side_effect = socket.error(61, 'socket error message')
        self.addCleanup(patch.stopall)
        with self.assertRaises(BrokenPromise):
            bok_choy.browser.browser()
        self.assertEqual(patch_object.call_count, 3)


class TestSaveFiles(TestCase):

    def setUp(self):
        super(TestSaveFiles, self).setUp()

        # Create a temp directory to save the files to
        tempdir_path = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(tempdir_path))

        # Take a screenshot of a page
        browser = bok_choy.browser.browser()
        self.addCleanup(browser.quit)
        self.browser = browser
        self.tempdir_path = tempdir_path

    def test_save_screenshot(self):
        browser = self.browser
        tempdir_path = self.tempdir_path

        # Configure the screenshot directory using an environment variable
        os.environ['SCREENSHOT_DIR'] = tempdir_path
        ButtonPage(browser).visit()
        bok_choy.browser.save_screenshot(browser, 'button_page')

        # Check that the file was created
        expected_file = os.path.join(tempdir_path, 'button_page.png')
        self.assertTrue(os.path.isfile(expected_file))

        # Check that the file is not empty
        self.assertGreater(os.stat(expected_file).st_size, 100)

    def test_save_driver_logs(self):
        browser = self.browser
        tempdir_path = self.tempdir_path

        # Configure the driver log directory using an environment variable
        os.environ['SELENIUM_DRIVER_LOG_DIR'] = tempdir_path
        JavaScriptPage(browser).visit()
        bok_choy.browser.save_driver_logs(browser, 'js_page')

        # Check that the files were created.
        # Note that the 'client' and 'server' log files will be empty.
        log_types = ['browser', 'driver', 'client', 'server']
        for log_type in log_types:
            expected_file = os.path.join(tempdir_path, 'js_page_{}.log'.format(log_type))
            self.assertTrue(os.path.isfile(expected_file))

    def test_save_source(self):
        browser = self.browser
        tempdir_path = self.tempdir_path

        # Configure the saved source directory using an environment variable
        os.environ['SAVED_SOURCE_DIR'] = tempdir_path
        ButtonPage(browser).visit()
        bok_choy.browser.save_source(browser, 'button_page')

        # Check that the file was created
        expected_file = os.path.join(tempdir_path, 'button_page.html')
        self.assertTrue(os.path.isfile(expected_file))

        # Check that the file is not empty
        self.assertGreater(os.stat(expected_file).st_size, 100)
