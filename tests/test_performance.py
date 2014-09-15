"""
Test basic performance report functionality
NOTE: To run these tests, browsermob-proxy-2.0-beta-9 must be installed

These aren't real unittests, just some sample scenarios.
"""

from bok_choy.web_app_test import WebAppTest, with_cache
from bok_choy.performance import MethodNotEnabledInCurrentMode
from .pages import ButtonPage, TextFieldPage
from nose.plugins.attrib import attr
from unittest import expectedFailure
import json

import os
# Set the default har capture method to 'error'
os.environ['BOK_CHOY_HAR_MODE'] = 'error'
os.environ['BROWSERMOB_PROXY_PORT'] = '8000'

def har_files():
    return os.listdir(os.environ.get('BOK_CHOY_HAR_DIR', ''))


class HarCaptureTestBase(WebAppTest):
    """
    CaptureHarOnErrorTest
    """

    def visit_pages(self):
        page = ButtonPage(self.browser)
        page.visit()

        page2 = TextFieldPage(self.browser)
        page2.visit()

    def setUp(self):
        # Adding as extra 'Cleanup',  because we have to wait for other
        # cleanup to happen before checking the har folder. Since cleanup
        # is LIFO, add the inspecting function first to ensure it is
        # executed last.
        self.should_capture = bool()
        self.addCleanup(self._inspect_har_files)
        self.inspect_har_content = False
        self.addCleanup(self._inspect_har_content)
        super(HarCaptureTestBase, self).setUp()

    def _inspect_har_files(self):
        # A list of booleans, each item representing if the file is a match.
        matched = [filename for filename in har_files() if self.id() in filename]
        self.assertEqual(self.should_capture, len(matched))

    def _inspect_har_content(self):
        # Additional check for this one to make sure that data is actually captured
        if self.inspect_har_content:
            har_file = None
            for filename in har_files():
                if self.id() in filename:
                    har_file = filename
                    break

            with open(os.path.join(os.environ.get('BOK_CHOY_HAR_DIR', ''), har_file)) as f:
                har_contents = json.load(f)

            self.assertTrue('status' in har_contents['log']['entries'][0]['response'].keys())


@attr(har_mode='explicit')
class ExplicitHarCaptureTest(HarCaptureTestBase):
    """
    How the har_mode is set: using the nose @attr decorator. This should override
    any environment setting. Note that this will only work if the `TestClass` is
    decorated, not the `test_case`.
    """
    @expectedFailure
    def test_har_is_not_captured_in_explicit_mode(self):
        self.should_capture = 0
        self.visit_pages()
        self.assertTrue(False)

    def test_capture_har_explicitly(self):
        self.should_capture = 1
        self.har_capturer.add_page(self.browser, 'ButtonPage')
        page = ButtonPage(self.browser)
        page.visit()

        self.har_capturer.add_page(self.browser, 'TextFieldPage')
        page2 = TextFieldPage(self.browser)
        page2.visit()
        page2.enter_text('testing')
        self.har_capturer.save_har(self.browser)

    @with_cache
    def test_capture_har_explicitly_with_cache(self):
        self.should_capture = 4
        self.har_capturer.add_page(self.browser, 'ButtonPage')
        page = ButtonPage(self.browser)
        page.visit()
        self.har_capturer.save_har(self.browser, self.id()+'_1')


        self.har_capturer.add_page(self.browser, 'TextFieldPage')
        page2 = TextFieldPage(self.browser)
        page2.visit()
        page2.enter_text('testing')
        self.har_capturer.save_har(self.browser, self.id()+'_2')


@attr(har_mode='auto')
class AutoHarCaptureTest(HarCaptureTestBase):
    """
    How the har_mode is set: using the nose @attr decorator. This should override
    any environment setting. Note that this will only work if the `TestClass` is
    decorated, not the `test_case`.
    """
    def test_har_is_captured_on_success_in_auto_mode(self):
        self.should_capture = 1
        self.inspect_har_content = True
        self.visit_pages()
        self.assertTrue(True)

    @expectedFailure
    def test_har_is_captured_on_failure_in_auto_mode(self):
        self.should_capture = 1
        self.visit_pages()
        self.assertTrue(False)

    @with_cache
    def test_two_hars_captured_on_success_in_auto_mode_with_cache(self):
        self.should_capture = 2
        self.visit_pages()
        self.assertTrue(True)


class ErrorHarCaptureTest(HarCaptureTestBase):
    """
    How the har_mode is set: using environment var `BOK_CHOY_HAR_MODE`. This can
    be overridden for an individual test class using the @attr decorator from 
    the nose.plugin.attrib module.
    """
    @expectedFailure
    def test_har_is_captured_on_error_in_error_mode(self):
        self.should_capture = 1
        self.visit_pages()
        raise Exception('Raising generic exception so that this test will error.')

    @expectedFailure
    def test_har_is_captured_on_failure_in_error_mode(self):
        self.should_capture = 1
        self.visit_pages()
        self.assertTrue(False)

    def test_har_is_not_captured_on_success_in_error_mode(self):
        self.should_capture = 0
        self.visit_pages()
        self.assertTrue(True)

    def test_explicit_har_capture_doesnt_work_in_error_mode(self):
        self.should_capture = 0

        # Try to save one when we shouldn't be able to.
        with self.assertRaises(MethodNotEnabledInCurrentMode):
            self.har_capturer.add_page(self.browser, 'ButtonPage')

        # Try to save one when we shouldn't be able to.
        with self.assertRaises(MethodNotEnabledInCurrentMode):
            self.har_capturer.save_har(self.browser)
