"""
Tests the representation of site pages.
"""

from __future__ import absolute_import

from unittest import TestCase

from mock import Mock

from bok_choy.page_object import PageObject, PageLoadError, unguarded, WrongPageError
from bok_choy.promise import BrokenPromise
from tests.pages import SitePage


class InvalidURLPage(SitePage):
    """
    Create a page that will return a malformed URL.
    """
    url = "http://localhost:/invalid"


class NeverOnPage(SitePage):
    """
    Create a page that never successfully loads.
    """
    url = "http://localhost/never_on"

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
                msg="Url: {0}, Expected {1} but got {2}".format(url, is_valid, returned_val)
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
