"""
Base implementation of the Page Object pattern.
See https://code.google.com/p/selenium/wiki/PageObjects
"""

import logging
import socket
import urlparse
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import defaultdict
from functools import wraps
from contextlib import contextmanager
from textwrap import dedent
from selenium.common.exceptions import WebDriverException

from .query import BrowserQuery
from .promise import Promise


class WrongPageError(Exception):
    """
    The page object reports that we're on the wrong page!
    """
    pass


class PageLoadError(Exception):
    """
    An error occurred while loading the page.
    """
    pass


def unguarded(method):
    """
    Mark a PageObject method as unguarded.

    Unguarded methods don't verify that the PageObject is
    on the current browser page before they execute

    Args:
        method (callable): The method to decorate.

    Returns:
        Decorated method
    """
    method._unguarded = True
    return method


def pre_verify(method):
    """
    Decorator that calls self._verify_page() before executing the decorated method

    Args:
        method (callable): The method to decorate.

    Returns:
        Decorated method
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        self._verify_page()
        return method(self, *args, **kwargs)
    return wrapper


class _PageObjectMetaclass(ABCMeta):
    """
    Decorates any callable attributes of the class
    so that they call self._verify_page() before executing.

    Excludes any methods marked as unguarded with the @unguarded
    decorator, any methods starting with _, or in the list ALWAYS_UNGUARDED.
    """
    ALWAYS_UNGUARDED = ['url', 'is_browser_on_page']

    def __new__(mcs, cls_name, cls_bases, cls_attrs):
        for name, attr in cls_attrs.items():
            # Skip methods marked as unguarded
            if getattr(attr, '_unguarded', False) or name in mcs.ALWAYS_UNGUARDED:
                continue

            # Skip private methods
            if name.startswith('_'):
                continue

            # Skip class attributes that are classes themselves
            if isinstance(attr, type):
                continue

            is_property = isinstance(attr, property)

            # Skip non-callable attributes
            if not (callable(attr) or is_property):
                continue

            if is_property:
                # For properties, wrap each of the sub-methods separately
                property_methods = defaultdict(None)
                for fn_name in ('fdel', 'fset', 'fget'):
                    prop_fn = getattr(cls_attrs[name], fn_name, None)
                    if prop_fn is not None:
                        # Check for unguarded properties
                        if getattr(prop_fn, '_unguarded', False):
                            property_methods[fn_name] = prop_fn
                        else:
                            property_methods[fn_name] = pre_verify(prop_fn)
                cls_attrs[name] = property(**property_methods)
            else:
                cls_attrs[name] = pre_verify(attr)

        return super(_PageObjectMetaclass, mcs).__new__(mcs, cls_name, cls_bases, cls_attrs)


class PageObject(object):
    """
    Encapsulates user interactions with a specific part
    of a web application.

    The most important thing is this:
    Page objects encapsulate Selenium.

    If you find yourself writing CSS selectors in tests,
    manipulating forms, or otherwise interacting directly
    with the web UI, stop!

    Instead, put these in a :class:`PageObject` subclass :)

    PageObjects do their best to verify that they are only
    used when the browser is on a page containing the object.
    To do this, they will call :meth:`is_browser_on_page` before executing
    any of their methods, and raise a :class:`WrongPageError` if the
    browser isn't on the correct page.

    Generally, this is the right behavior. However, at times it
    will be useful to not verify the page before executing a method.
    In those cases, the method can be marked with the :func:`unguarded`
    decorator. Additionally, private methods (those beginning with `_`)
    are always unguarded.

    Class or instance properties are never guarded. However, methods
    marked with the :func:`property` are candidates for being guarded.
    To make them unguarded, you must mark the getter, setter, and deleter
    as :func:`unguarded` separately, and those decorators must be applied before
    the :func:`property` decorator.

    Correct::

        @property
        @unguarded
        def foo(self):
            return self._foo

    Incorrect::

        @unguarded
        @property
        def foo(self):
            return self._foo
    """

    __metaclass__ = _PageObjectMetaclass

    def __init__(self, browser):
        """
        Initialize the page object to use the specified browser instance.

        Args:
            browser (selenium.webdriver): The Selenium-controlled browser.

        Returns:
            PageObject
        """
        self.browser = browser

    @abstractmethod
    def is_browser_on_page(self):
        """
        Check that we are on the right page in the browser.
        The specific check will vary from page to page,
        but usually this amounts to checking the:

            1) browser URL
            2) page title
            3) page headings

        Returns:
            A `bool` indicating whether the browser is on the correct page.
        """
        return False

    @abstractproperty
    def url(self):
        """
        Return the URL of the page.  This may be dynamic,
        determined by configuration options passed to the
        page object's constructor.

        Some pages may not be directly accessible:
        perhaps the page object represents a "navigation"
        component that occurs on multiple pages.
        If this is the case, subclasses can return `None`
        to indicate that you can't directly visit the page object.
        """
        return None

    @unguarded
    def warning(self, msg):
        """
        Subclasses call this to indicate that something unexpected
        occurred while interacting with the page.

        Page objects themselves should never make assertions or
        raise exceptions, but they can issue warnings to make
        tests easier to debug.

        Args:
            msg (str): The message to log as a warning.

        Returns:
            None
        """
        log = logging.getLogger(self.__class__.__name__)
        log.warning(msg)

    @unguarded
    def visit(self):
        """
        Open the page containing this page object in the browser.

        Some page objects may not provide a URL, in which case
        a `NotImplementedError` will be raised.

        Raises:
            PageLoadError: The page did not load successfully.
            WrongPageError: The browser is not on the correct page.
            NotImplementedError: The page object does not provide a URL to visit.

        Returns:
            PageObject
        """
        if self.url is None:
            raise NotImplementedError("Page {} does not provide a URL to visit.".format(self))

        # Validate the URL
        if not self.validate_url(self.url):
            raise PageLoadError("Invalid URL: '{}'".format(self.url))

        # Visit the URL
        try:
            self.browser.get(self.url)
        except (WebDriverException, socket.gaierror):
            raise PageLoadError("Could not load page '{!r}' at URL '{}'".format(
                self, self.url
            ))

        # Ask the page object to verify that the correct page loaded
        self._verify_page()

        # Return the page object, so that the caller can chain the call with an action:
        # Example: FooPage.visit().do_something()
        return self

    @classmethod
    @unguarded
    def validate_url(cls, url):
        """
        Return a boolean indicating whether the URL has a protocol and hostname.
        If a port is specified, ensure it is an integer.

        Arguments:
            url (str): The URL to check.

        Returns:
            Boolean indicating whether the URL has a protocol and hostname.
        """
        result = urlparse.urlsplit(url)

        # Check that we have a protocol and hostname
        if not result.scheme or not result.netloc:
            return False

        # Check that the port is an integer
        try:
            if result.port is not None:
                int(result.port)
        except ValueError:
            return False
        else:
            return True

    def _verify_page(self):
        """
        Ask the page object if we're on the right page;
        if not, raise a `WrongPageError`.
        """
        if not self.is_browser_on_page():
            msg = "Not on the correct page to use {!r}".format(self)
            raise WrongPageError(msg)

    @unguarded
    def wait_for_page(self, timeout=30):
        """
        Block until the page loads, then returns the page.
        Useful for ensuring that we navigate successfully to a particular page.

        Keyword Args:
            timeout (int): The number of seconds to wait for the page before timing out with an exception.

        Raises:
            BrokenPromise: The timeout is exceeded without the page loading successfully.
        """
        return Promise(
            lambda: (self.is_browser_on_page(), self), "loaded page {!r}".format(self),
            timeout=timeout
        ).fulfill()

    def q(self, **kwargs):
        """
        Construct a query on the browser.

        Example usages:

        .. code:: python

            self.q(css="div.foo").first.click()
            self.q(xpath="/foo/bar").text

        Keyword Args:
            css: A CSS selector.
            xpath: An XPath selector.

        Returns:
            BrowserQuery
        """
        return BrowserQuery(self.browser, **kwargs)

    @contextmanager
    def handle_alert(self, confirm=True):
        """
        Context manager that ensures alerts are dismissed.

        Example usage:

        .. code:: python

            with self.handle_alert():
                self.q(css='input.submit-button').first.click()

        Keyword Args:
            confirm (bool): Whether to confirm or cancel the alert.

        Returns:
            None
        """

        # Before executing the `with` block, stub the confirm/alert functions
        script = dedent("""
            window.confirm = function() {{ return {0}; }};
            window.alert = function() {{ return; }};
        """.format("true" if confirm else "false")).strip()
        self.browser.execute_script(script)

        # Execute the `with` block
        yield
