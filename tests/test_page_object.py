"""
Tests the representation of site pages.
"""

from __future__ import absolute_import

import logging
from unittest import TestCase

import pytest
from mock import Mock
from selenium.common.exceptions import WebDriverException

from bok_choy.page_object import PageObject, PageLoadError, unguarded, WrongPageError
from bok_choy.promise import BrokenPromise
from tests.pages import ButtonPage, SitePage


class InvalidPortPage(SitePage):
    """
    Create a page that will return a URL with an invalid port.
    """
    url = "http://localhost:8o/invalid"


class InvalidURLPage(SitePage):
    """
    Create a page that will return a malformed URL.
    """
    url = "http://localhost:/invalid"


class MissingHostnamePage(SitePage):
    """
    Create a page that will return a URL with no hostname.
    """
    url = "http:///invalid"


class NeverOnPage(SitePage):
    """
    Create a page that never successfully loads.
    """
    url = "http://localhost/never_on"
    class_attr = ButtonPage

    def is_browser_on_page(self):
        return False

    @unguarded
    def wait_for_page(self, timeout=30):
        # This page should never load.
        raise BrokenPromise(None)

    def _private_method(self):
        """Example of a no-op private method."""
        pass

    def guarded_method(self):
        """
        A no-op method which waits for the page to finish loading.
        """
        pass

    @unguarded
    def unguarded_method(self):
        """
        A no-op method which does not wait for the page to finish loading.
        """
        pass

    @property
    def guarded_property(self):
        """
        A property which waits for the page to finish loading before evaluating.
        """
        return True

    @property
    @unguarded
    def unguarded_property(self):
        """
        A property which does not wait for the page to finish loading before evaluating.
        """
        return True


class NoUrlProvidedPage(SitePage):
    """
    Page that you can't directly navigate to, because
    no URL is provided.
    """
    url = None


class PageObjectTest(TestCase):
    """
    Tests of ``PageObject`` class functionality.
    """
    def test_invalid_url_exception(self):
        with self.assertRaises(PageLoadError):
            InvalidURLPage(Mock()).visit()

    def test_validate_url(self):
        """
        Check error handling for malformed url.
        URLs must have a protocol and host; if a port is specified,
        it must use the correct syntax.
        """
        for url, is_valid in [
                ("", False), ("invalid", False), ("/invalid", False), ("http://localhost:", False),
                ("http://localhost:/invalid", False), ("://localhost/invalid", False),
                ("http://localhost", True), ("http://localhost/test", True),
                ("http://localhost:8080", True), ("http://localhost:8080/test", True),
                ("http://user:pass@localhost/test", True), ("http://user:pass@localhost:8080/test", True)
        ]:
            returned_val = PageObject.validate_url(url)
            self.assertEqual(
                returned_val,
                is_valid,
                msg=u"Url: {0}, Expected {1} but got {2}".format(url, is_valid, returned_val)
            )

    def test_guarded_methods(self):
        never_on = NeverOnPage(Mock())

        self.assertFalse(never_on.is_browser_on_page())
        assert never_on.url
        never_on.unguarded_method()
        never_on._private_method()  # pylint: disable=protected-access
        assert never_on.unguarded_property

        with self.assertRaises(WrongPageError):
            never_on.guarded_method()

        with self.assertRaises(WrongPageError):
            assert never_on.guarded_property

    def test_visit_no_url(self):

        # Can't visit a page with no URL specified
        with self.assertRaises(NotImplementedError):
            NoUrlProvidedPage(Mock()).visit()

    def test_visit_timeout(self):

        # If the page doesn't load before the timeout, PageLoadError is raised
        with self.assertRaises(PageLoadError):
            NeverOnPage(Mock()).visit()


def test_invalid_port_exception(caplog):
    with pytest.raises(PageLoadError):
        InvalidPortPage(Mock()).visit()
    assert u'uses an invalid port' in caplog.text


def test_missing_hostname_exception(caplog):
    with pytest.raises(PageLoadError):
        MissingHostnamePage(Mock()).visit()
    assert u'is missing a hostname' in caplog.text


def test_never_loads(caplog):
    attrs = {'execute_script.return_value': False}
    browser = Mock(**attrs)
    page = ButtonPage(browser)
    with pytest.raises(BrokenPromise):
        page.wait_for_page(timeout=1)
    assert u'document.readyState does not become complete for following url' in caplog.text


def test_page_load_exception(caplog):
    attrs = {'get.side_effect': WebDriverException('Boom!')}
    browser = Mock(**attrs)
    page = ButtonPage(browser)
    with pytest.raises(PageLoadError):
        page.visit()
    assert u'Unexpected page load exception' in caplog.text


def test_retry_errors(caplog):
    def promise_check_func():
        """
        Check function which continuously fails with a WebDriverException until timeout
        """
        raise WebDriverException('Boom!')
    page = ButtonPage(Mock())
    with pytest.raises(BrokenPromise):
        page.wait_for(promise_check_func, 'Never succeeds', timeout=1)
    assert u'Exception ignored during retry loop' in caplog.text


def test_warning(caplog):
    page = SitePage(Mock())
    page.warning(u'Scary stuff')
    assert ('SitePage', logging.WARN, u'Scary stuff') in caplog.record_tuples
