"""
Web application user interface.
Encapsulates tests from interacting directly with Selenium.
"""
import socket
from collections import Mapping
import splinter
from .promise import EmptyPromise, fulfill

import logging
LOGGER = logging.getLogger(__name__)

from .browser import browser


class WebAppUIConfigError(Exception):
    """
    An error occurred in the configuration of
    the web app UI.
    """
    pass


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


class WebAppUI(Mapping):
    """
    Base class for a web application user interface.

    A web application UI is a collection of pages, which
    the user can interact with.
    """

    _browser = None
    _page_object_dict = None

    def __init__(self, page_object_classes, tags):
        """
        Create an object to interact with a web application's
        user interface.

        Uses environment variables to create the browser
        (using local browser or SauceLabs).

        The browser will be shared by all pages in the web app.

        `page_object_classes` is a list of `PageObject` subclasses
        to include in this web app UI.  Each page object class
        defines the name used to access it; these names must
        be unique among page objects in the list.

        `tags` is a list of tags to apply to the SauceLabs
        job (if the environment is configured to use SauceLabs)

        Raises a `WebAppUIConfigError` if page object names
        are not unique.

        Raises a `BrowserConfigError` if environment variables
        for browser configuration are invalid.
        """

        # Create the browser, either locally or using SauceLabs
        self._browser = browser(tags)

        try:

            # Create the mapping from page object names to
            # page object instances.
            # If we find duplicate names, raise an exception.
            self._page_object_dict = dict()
            for clz in page_object_classes:

                # Instantiate a new page object instance
                # and configure it reference this object (the WebAppUI)
                page = clz(self, self._browser)

                if page.name in self._page_object_dict:
                    msg = "Duplicate page object name: {0}".format(page.name)
                    raise WebAppUIConfigError(msg)

                else:
                    self._page_object_dict[page.name] = page

        # Quit out of the browser so it doesn't
        # keep running after we fail.
        except:
            try:
                self.quit_browser()
            except Exception as ex:
                LOGGER.warning("Could not quit browser: {0}".format(ex))

            # Re-raise any exceptions
            raise


    def visit(self, page_name, **kwargs):
        """
        Open the page with the specified `page_name` in the browser.
        `kwargs` is a parameter dict passed to the page object's
        `url()` method.

        Raises an `WebAppUIConfigError` if the page object doesn't exist.

        Raises a `PageLoadError` if an HTTP error occurred while accessing
        the page.

        Raises a `WrongPageError` if after visiting the page, the page object
        says it's not on the right page.

        Some page objects may not implement the `url()` method;
        in that case, a `NotImplementedError` will be raised.

        Once you've visited a page, you should interact with it
        using bracket syntax:

        .. code:: python

            # `ui` is a WebAppUI instance
            ui['foo_page'].bar()

        The bracket access provides additional sanity checks
        and waits to ensure that you can interact
        with the page.
        """
        page = self._get_page_or_error(page_name)

        # Ask the page for its url
        # This may raise a NotImplementedError
        # if the page isn't reachable from a specific URL
        url = page.url(**kwargs)

        # Visit the URL
        try:
            self._browser.visit(url)
        except splinter.request_handler.status_code.HttpResponseError as ex:
            msg = "Could not load page '{0}' with parameters {1} at URL '{2}'.  Status code {3}, '{4}'".format(
                page_name, kwargs, url, ex.status_code, ex.reason
            )
            raise PageLoadError(msg)
        except socket.gaierror:
            raise PageLoadError("Could not load page '{0}' with parameters {1} at URL '{2}'".format(
                page_name, kwargs, url
            ))

        # Ask the page object to verify that the correct page loaded
        self._verify_page(page)

    def wait_for_page(self, page_name, timeout=30):
        """
        Block until the page named `page_name` loads.

        Useful for ensuring that we navigate successfully from the current
        page to the next page.

        Raises a `WebAppUIConfigError` if the page object doesn't exist.
        Raises a `BrokenPromise` exception if the page fails to load within `timeout` seconds.
        """
        next_page = self._get_page_or_error(page_name)
        return fulfill(
            EmptyPromise(
                next_page.is_browser_on_page,
                "loaded page '{0}'".format(page_name)
        ))

    def __getitem__(self, key):
        """
        Return the page object with the name `key`.
        Also asks the page object to verify that it is on the correct page.

        Since these are the kind of sanity checks you generally
        want to perform before interacting with a page,
        it's best to call page object methods like this:

            # `ui` is a WebAppUI instance
            ui['foo_page'].bar()

        This guarantees that basic assumptions about the page
        are met before trying to interact with it.

        `PageObject` instances define their own names,
        which must be unique among pages in the `WebAppUI`.

        Raises an `WebAppUIConfigError` if the page object doesn't exist.
        """
        page = self._get_page_or_error(key)

        # Raise an error if we're on the wrong page
        self._verify_page(page)

        # Basic sanity checks passed; the tests can now interact
        # with the web app using the page object.
        return page

    def __iter__(self):
        """
        Iterator for traversing `PageObject` instances
        in the `WebAppUI`.
        """
        return iter(self._page_object_dict)

    def __len__(self):
        """
        Number of `PageObject` instances in the `WebAppUI`.
        """
        return len(self._page_object_dict)

    def __repr__(self):
        """
        Useful for debugging.
        """
        return "<WebAppUI>: " + repr(self._page_object_dict)

    def quit_browser(self):
        """
        Quit the browser used to access the web app UI.
        You are responsible for calling this before the program
        terminates.

        Once this method is called, you can no longer use
        page objects in this web app UI!
        """
        self._browser.quit()

    def _get_page_or_error(self, page_name):
        """
        Retrieve the page object, or raise
        a `WebAppUIConfigError` if no such page
        object can be found.
        """
        try:
            return self._page_object_dict[page_name]
        except KeyError:
            msg = "Could not find page object for '{0}'".format(page_name)
            raise WebAppUIConfigError(msg)

    def _verify_page(self, page_object):
        """
        Ask the page object if we're on the right page;
        if not, raise a `WrongPageError`.
        """
        if not page_object.is_browser_on_page():
            msg = "Not on the correct page to use '{}'".format(page_object.name)
            raise WrongPageError(msg)
