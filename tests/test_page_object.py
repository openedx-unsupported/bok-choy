from mock import Mock
from unittest import TestCase

from bok_choy.page_object import PageObject, PageLoadError, unguarded, WrongPageError
from bok_choy.promise import BrokenPromise
from .pages import SitePage


class InvalidURLPage(SitePage):
    """
    Create a page that will return a malformed URL.
    """
    url = "http://localhost:/invalid"


class NeverOnPage(SitePage):

    url = "http://localhost/never_on"

    def is_browser_on_page(self):
        return False

    @unguarded
    def wait_for_page(self):
        # This page should never load.
        raise BrokenPromise(None)

    def _private_method(self):
        pass

    def guarded_method(self):
        pass

    @unguarded
    def unguarded_method(self):
        pass

    @property
    def guarded_property(self):
        pass

    @property
    @unguarded
    def unguarded_property(self):
        pass


class NoUrlProvidedPage(SitePage):
    """
    Page that you can't directly navigate to, because
    no URL is provided.
    """
    url = None


class PageObjectTest(TestCase):
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
            ("", False), ("invalid", False), ("/invalid", False),
            ("http://localhost:/invalid", False), ("://localhost/invalid", False),
            ("http://localhost", True), ("http://localhost/test", True),
            ("http://localhost:8080", True), ("http://localhost:8080/test", True)
        ]:
            self.assertEquals(PageObject.validate_url(url), is_valid)

    def test_guarded_methods(self):
        never_on = NeverOnPage(Mock())

        self.assertFalse(never_on.is_browser_on_page())
        never_on.url
        never_on.unguarded_method()
        never_on._private_method()
        never_on.unguarded_property

        with self.assertRaises(WrongPageError):
            never_on.guarded_method()

        with self.assertRaises(WrongPageError):
            never_on.guarded_property

    def test_visit_no_url(self):

        # Can't visit a page with no URL specified
        with self.assertRaises(NotImplementedError):
            NoUrlProvidedPage(Mock()).visit()

    def test_visit_timeout(self):

        # If the page doesn't load before the timeout, PageLoadError is raised
        with self.assertRaises(PageLoadError):
            NeverOnPage(Mock()).visit()

