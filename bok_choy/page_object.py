"""
Base implementation of the Page Object pattern.
See https://code.google.com/p/selenium/wiki/PageObjects
"""

from abc import ABCMeta, abstractproperty, abstractmethod
import logging
from .safe_selenium import SafeSelenium


class PageObject(SafeSelenium):
    """
    Encapsulates user interactions with a specific part
    of a web application.

    Usually, you will rely on `WebAppInterface`
    to instantiate the page object and won't
    need to call this method directly.

    The most important thing is this:
    Page objects encapsulate Selenium.

    If you find yourself writing CSS selectors in tests,
    manipulating forms, or otherwise interacting directly
    with the web UI, stop!

    Instead, put these in a `PageObject` subclass :)
    """

    __metaclass__ = ABCMeta

    def __init__(self, ui, browser):
        """
        Initialize the page object to use `ui` (a `WebAppUI` instance)
        and `browser` (a `Browser` instance).
        """
        super(PageObject, self).__init__(browser)
        self._ui = ui

    @property
    def ui(self):
        """
        The `WebAppUI` instance associated with this page.
        Pages can use this to reference other pages.
        """
        return self._ui

    @abstractproperty
    def name(self):
        """
        Define a name used to access the page object.
        This is used by `WebAppInterface` to uniquely identify
        page objects and provide a succinct way to
        access them.
        """
        return ""

    @abstractmethod
    def is_browser_on_page(self):
        """
        Check that we are on the right page in the browser.
        The specific check will vary from page to page,
        but usually this amounts to checking the:

            1) browser URL
            2) page title
            3) page headings

        Return a `bool` indicating whether the browser is on
        the correct page.
        """
        return False

    @abstractmethod
    def url(self, **kwargs):
        """
        Return the URL of the page.

        Pages may need different parameters to figure out
        which URL to load; they can access those parameters
        from the `kwargs` dict.

        Some pages may not be directly accessible:
        perhaps the page object represents a "navigation"
        component that occurs on multiple pages.
        If this is the case, subclasses can raise a
        `NotImplemented` error to indicate that you
        can't directly visit the page object.
        """
        raise NotImplemented

    def warning(self, msg):
        """
        Subclasses call this to indicate that something unexpected
        occurred while interacting with the page.

        Page objects themselves should never make assertions or
        raise exceptions, but they can issue warnings to make
        tests easier to debug.
        """
        log = logging.getLogger(self.__class__.__name__)
        log.warning(msg)
