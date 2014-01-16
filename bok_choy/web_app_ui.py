"""
Web application user interface.
Encapsulates tests from interacting directly with Selenium.
"""
import os

import logging
LOGGER = logging.getLogger(__name__)

from .browser import browser


class WebAppUIConfigError(Exception):
    """
    An error occurred in the configuration of
    the web app UI.
    """
    pass


class WebAppUI(object):
    """
    Base class for a web application user interface.

    A web application UI is a collection of pages, which
    the user can interact with.
    """

    _browser = None
    _page_object_dict = None

    def __init__(self, tags):
        """
        Create an object to interact with a web application's
        user interface.

        Uses environment variables to create the browser
        (using local browser or SauceLabs).

        The browser will be shared by all pages in the web app.

        `tags` is a list of tags to apply to the SauceLabs
        job (if the environment is configured to use SauceLabs)

        Raises a `WebAppUIConfigError` if page object names
        are not unique.

        Raises a `BrowserConfigError` if environment variables
        for browser configuration are invalid.
        """

        # Create the browser, either locally or using SauceLabs
        self._browser = browser(tags)

    @property
    def browser(self):
        """
        Return the browser object used by this `WebAppUI`.
        """
        return self._browser

    def __repr__(self):
        """
        Useful for debugging.
        """
        return "<WebAppUI>"

    def quit_browser(self):
        """
        Quit the browser used to access the web app UI.
        You are responsible for calling this before the program
        terminates.

        Once this method is called, you can no longer use
        page objects in this web app UI!
        """
        self._browser.quit()

    def save_screenshot(self, name):
        """
        Save a screenshot of the browser.

        The location of the screenshot can be configured
        by the environment variable `SCREENSHOT_DIR`.  If not set,
        this defaults to the current working directory.

        `name` is a name for the screenshot, which will be used
        in the output file name.
        """
        image_name = os.path.join(
            os.environ.get('SCREENSHOT_DIR', ''), name + '.png'
        )
        self._browser.driver.save_screenshot(image_name)

