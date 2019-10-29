"""
Tests browser instantiation, selection, etc
"""
from __future__ import absolute_import

import tempfile
import shutil
import os
import socket
from unittest import TestCase
import pytest

from mock import patch
from selenium import webdriver
from selenium.common.exceptions import WebDriverException

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
        # In spite of the name, 'default_preferences' represents the preferences
        # that are in place on the browser. (The underlying preferences start
        # with default_preferences and are updated in-place.)
        preferences = browser.profile.default_preferences
        self.assertEqual(preferences['browser.startup.homepage'], 'about:blank')
        self.assertEqual(preferences['startup.homepage_welcome_url'], 'about:blank')
        self.assertEqual(preferences['startup.homepage_welcome_url.additional'], 'about:blank')
        self.assertFalse(preferences['app.update.enabled'])
        self.assertTrue(preferences['plugins.hide_infobar_for_outdated_plugin'])
        self.assertFalse(preferences['datareporting.healthreport.service.enabled'])
        self.assertFalse(preferences['datareporting.policy.dataSubmissionEnabled'])
        self.assertFalse(preferences['toolkit.crashreporter.enabled'])

    @patch.dict(os.environ, {'SELENIUM_BROWSER': 'firefox'})
    def test_customize_firefox_preferences(self):
        def customize_preferences(profile):
            """
            Disable the limits on script execution time.
            """
            profile.set_preference('dom.max_chrome_script_run_time', 0)
            profile.set_preference('dom.max_script_run_time', 0)
        bok_choy.browser.add_profile_customizer(customize_preferences)
        self.addCleanup(bok_choy.browser.clear_profile_customizers)
        browser = bok_choy.browser.browser()
        self.addCleanup(browser.quit)
        # In spite of the name, 'default_preferences' represents the preferences
        # that are in place on the browser. (The underlying preferences start
        # with default_preferences and are updated in-place.)
        preferences = browser.profile.default_preferences
        assert preferences['dom.max_chrome_script_run_time'] == 0
        assert preferences['dom.max_script_run_time'] == 0

    @patch.dict(os.environ, {'SELENIUM_BROWSER': 'phantomjs'})
    def test_phantom_browser(self):
        browser = bok_choy.browser.browser()
        self.addCleanup(browser.quit)
        self.assertIsInstance(browser, webdriver.PhantomJS)

    @patch.dict(os.environ, {'SELENIUM_BROWSER': 'invalid'})
    def test_invalid_browser_name(self):
        with self.assertRaises(bok_choy.browser.BrowserConfigError):
            bok_choy.browser.browser()

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
        browser_kwargs_tuple = bok_choy.browser._local_browser_class('firefox')  # pylint: disable=protected-access
        assert 'firefox_profile' in browser_kwargs_tuple[2]
        patch_object.assert_called_with('/foo/path')

    @patch.dict(os.environ, {'FIREFOX_PROFILE_PATH': ''})
    def test_no_custom_firefox_profile(self):
        patch_object = patch.object(webdriver, 'FirefoxProfile').start()
        self.addCleanup(patch.stopall)
        browser_kwargs_tuple = bok_choy.browser._local_browser_class('firefox')  # pylint: disable=protected-access
        assert 'firefox_profile' in browser_kwargs_tuple[2]
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

    @patch.dict(os.environ, {
        'SELENIUM_BROWSER': 'firefox',
        'SELENIUM_HOST': '127.0.0.1',
        'SELENIUM_PORT': '80',
    })
    def test_other_capabilities_loaded(self):
        """
        If additional desired capabilities are given,
         they should be sent to the remote WebDriver,
         but not override existing environment variable logic.
        """
        patch_object = patch('selenium.webdriver.Remote').start()
        self.addCleanup(patch.stopall)
        browser = bok_choy.browser.browser(other_caps={
            # Intentionally different, should not be changed
            'browserName': 'fhrome',
            'extra-data': '1234',
        })
        self.addCleanup(browser.quit)
        self.assertEqual(patch_object.call_count, 1)
        desired_caps = patch_object.call_args[1]['desired_capabilities']
        # browserName in other_caps should not have overriden env var mapping behavior
        self.assertEqual(desired_caps['browserName'], 'firefox')
        self.assertEqual(desired_caps['extra-data'], '1234')


class TestFirefoxBrowserConfig(TestCase):
    """ Tests for configuring the firefox path and log file."""
    @staticmethod
    def verify_config(custom_path=None, custom_log=None):
        """Verify that the configurations were applied correctly."""
        browser_kwargs_tuple = bok_choy.browser._local_browser_class('firefox')  # pylint: disable=protected-access
        if not custom_path and not custom_log:
            assert 'firefox_binary' not in browser_kwargs_tuple[2]

        else:
            ffb = browser_kwargs_tuple[2].get('firefox_binary')

            # Verifications for path handling
            if custom_path:
                assert ffb._start_cmd == custom_path  # pylint: disable=protected-access
            else:
                assert ffb._start_cmd == ffb._get_firefox_start_cmd()  # pylint: disable=protected-access

            # Verifications for log file handling
            log_file = ffb._log_file  # pylint: disable=protected-access
            if hasattr(log_file, 'read'):
                log_file = log_file.name
            if custom_log:
                assert log_file == custom_log
            else:
                assert log_file == '/dev/null'

    @patch.dict(os.environ, [('SELENIUM_FIREFOX_PATH', '/foo/path')])
    def test_custom_firefox_path(self):
        self.verify_config(custom_path='/foo/path')

    @patch.dict(os.environ, [('SELENIUM_FIREFOX_LOG', '/foo/file.log')])
    def test_custom_firefox_log(self):
        self.verify_config(custom_log='/foo/file.log')

    @patch.dict(os.environ, [('SELENIUM_FIREFOX_PATH', '/foo/path'), ('SELENIUM_FIREFOX_LOG', '/foo/file.log')])
    def test_custom_firefox_path_and_log(self):
        self.verify_config(custom_path='/foo/path', custom_log='/foo/file.log')

    @patch.dict(os.environ, {'SELENIUM_FIREFOX_PATH': ''})
    def test_empty_string_custom_ff_path(self):
        self.verify_config()

    @patch.dict(os.environ, [('SELENIUM_FIREFOX_LOG', '')])
    def test_empty_string_custom_ff_log(self):
        self.verify_config()


class TestSaveFiles(object):
    """
    Tests for saving files from the browser (including logs, page source, and
    screenshots).
    """
    tempdir_path = None
    browser = None

    def setup(self):
        """
        Create a temp directory to save the files to and instantiate the
        browser.
        """
        self.tempdir_path = tempfile.mkdtemp()
        self.browser = bok_choy.browser.browser()

    def teardown(self):
        """
        Remove the temp directory and quit the browser.
        """
        shutil.rmtree(self.tempdir_path)
        self.browser.quit()

    def test_save_screenshot(self):
        browser = self.browser
        tempdir_path = self.tempdir_path

        # Configure the screenshot directory using an environment variable
        os.environ['SCREENSHOT_DIR'] = tempdir_path
        ButtonPage(browser).visit()
        bok_choy.browser.save_screenshot(browser, 'button_page')

        # Check that the file was created
        expected_file = os.path.join(tempdir_path, 'button_page.png')
        assert os.path.isfile(expected_file)

        # Check that the file is not empty
        assert os.stat(expected_file).st_size > 100

    def test_save_screenshot_dir_not_set(self, caplog, monkeypatch):
        browser = self.browser
        monkeypatch.delenv('SCREENSHOT_DIR')
        bok_choy.browser.save_screenshot(browser, 'empty')
        assert 'The SCREENSHOT_DIR environment variable was not set; not saving a screenshot' in caplog.text

    def test_save_screenshot_unsupported(self, caplog):
        browser = 'Some driver without save_screenshot()'
        bok_choy.browser.save_screenshot(browser, 'button_page')
        assert 'Browser does not support screenshots.' in caplog.text

    def test_save_driver_logs_dir_not_set(self, caplog, monkeypatch):
        browser = self.browser
        monkeypatch.delenv('SELENIUM_DRIVER_LOG_DIR')
        bok_choy.browser.save_driver_logs(browser, 'empty')
        assert 'The SELENIUM_DRIVER_LOG_DIR environment variable was not set; not saving logs' in caplog.text

    @pytest.mark.skipif(os.environ.get('SELENIUM_BROWSER', 'firefox') != "firefox",
                        reason="Selenium driver logs are supported on non-firefox browsers")
    def test_save_driver_logs_unsupported(self):
        browser = self.browser
        tempdir_path = self.tempdir_path

        # Configure the driver log directory using an environment variable
        os.environ['SELENIUM_DRIVER_LOG_DIR'] = tempdir_path
        JavaScriptPage(browser).visit()
        bok_choy.browser.save_driver_logs(browser, 'js_page')

        # Check that no files were created.
        log_types = ['browser', 'driver', 'client', 'server']
        for log_type in log_types:
            expected_file = os.path.join(tempdir_path, 'js_page_{}.log'.format(log_type))
            assert not os.path.exists(expected_file)

    @pytest.mark.skipif(os.environ.get('SELENIUM_BROWSER', 'firefox') == "firefox",
                        reason="Selenium driver logs no longer supported on firefox")
    def test_save_driver_logs(self):
        browser = self.browser
        tempdir_path = self.tempdir_path

        # Configure the driver log directory using an environment variable
        os.environ['SELENIUM_DRIVER_LOG_DIR'] = tempdir_path
        JavaScriptPage(browser).visit()
        bok_choy.browser.save_driver_logs(browser, 'js_page')

        # Check that the files were created.
        # Note that the 'client' and 'server' log files will be empty.
        log_types = browser.log_types
        for log_type in log_types:
            expected_file = os.path.join(tempdir_path, 'js_page_{}.log'.format(log_type))
            assert os.path.isfile(expected_file)

    @pytest.mark.skipif(os.environ.get('SELENIUM_BROWSER', 'firefox') == "firefox",
                        reason="Selenium driver logs no longer supported on firefox")
    def test_save_driver_logs_exception(self, caplog):
        browser = self.browser
        tempdir_path = self.tempdir_path

        # Configure the driver log directory using an environment variable
        os.environ['SELENIUM_DRIVER_LOG_DIR'] = tempdir_path
        JavaScriptPage(browser).visit()
        with patch.object(browser, 'get_log', side_effect=Exception):
            bok_choy.browser.save_driver_logs(browser, 'js_page')

        # Check that no files were created.
        log_types = browser.log_types
        for log_type in log_types:
            expected_file = os.path.join(tempdir_path, u'js_page_{}.log'.format(log_type))
            assert not os.path.exists(expected_file)
            assert u"Could not save browser log of type '{}'.".format(log_type) in caplog.text

    def test_save_source(self):
        browser = self.browser
        tempdir_path = self.tempdir_path

        # Configure the saved source directory using an environment variable
        os.environ['SAVED_SOURCE_DIR'] = tempdir_path
        ButtonPage(browser).visit()
        bok_choy.browser.save_source(browser, 'button_page')

        # Check that the file was created
        expected_file = os.path.join(tempdir_path, 'button_page.html')
        assert os.path.isfile(expected_file)

        # Check that the file is not empty
        assert os.stat(expected_file).st_size > 100

    def test_save_source_missing_directory(self):
        shutil.rmtree(self.tempdir_path)
        os.environ['SAVED_SOURCE_DIR'] = self.tempdir_path
        ButtonPage(self.browser).visit()
        bok_choy.browser.save_source(self.browser, 'button_page')

        expected_file = os.path.join(self.tempdir_path, 'button_page.html')
        assert os.path.isfile(expected_file)

        # Check that the file is not empty
        assert os.stat(expected_file).st_size > 100

    def test_save_source_no_permission(self, caplog):
        os.environ['SAVED_SOURCE_DIR'] = '/does_not_exist'
        ButtonPage(self.browser).visit()
        bok_choy.browser.save_source(self.browser, 'button_page')

        expected_file = os.path.join(self.tempdir_path, 'button_page.html')
        assert not os.path.exists(expected_file)
        assert 'Could not save the browser page source' in caplog.text
