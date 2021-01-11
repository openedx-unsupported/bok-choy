"""
Tests for identifying XSS vulnerabilities.
This is currently done when the "q" method is called.
"""

import os
from unittest.mock import patch
import pytest

from bok_choy.page_object import XSSExposureError
from bok_choy.web_app_test import WebAppTest
from .pages import SitePage


class XSSExposureTest(WebAppTest):
    """
    Tests for identifying XSS vulnerabilities.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.site_page = None

    def _visit_page(self, page_name):
        """
        Instantiate a ``SitePage`` for the given base filename and visit it.
        """
        self.site_page = SitePage(self.browser)
        self.site_page.name = page_name
        self.site_page.visit()

    @patch.dict(os.environ, {'VERIFY_XSS': 'True'})
    def test_html_exposure(self):
        self._visit_page("xss_html")
        with pytest.raises(XSSExposureError) as excinfo:
            self.site_page.q(css='.unescaped')
        assert '2 XSS issue' in str(excinfo)

    @patch.dict(os.environ, {'VERIFY_XSS': 'True'})
    def test_js_exposure(self):
        self._visit_page("xss_js")
        with pytest.raises(XSSExposureError) as excinfo:
            self.site_page.q(css='.unescaped')
        assert '1 XSS issue' in str(excinfo)

    @patch.dict(os.environ, {'VERIFY_XSS': 'True'})
    def test_mixed_exposure(self):
        self._visit_page("xss_mixed")
        with pytest.raises(XSSExposureError) as excinfo:
            self.site_page.q(css='.unescaped')
        assert '2 XSS issue' in str(excinfo)

    @patch.dict(os.environ, {'VERIFY_XSS': 'True'})
    def test_escaped(self):
        self._visit_page("xss_safe")
        self.site_page.q(css='.escaped')

    @patch.dict(os.environ, {'VERIFY_XSS': 'False'})
    def test_xss_testing_disabled_explicitly(self):
        self._visit_page("xss_html")
        self.site_page.q(css='.unescaped')

    def test_xss_testing_disabled_by_default(self):
        self._visit_page("xss_html")
        self.site_page.q(css='.unescaped')
