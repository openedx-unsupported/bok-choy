"""
Utilities for checking network performance of a web application.
"""
import os
import json
import datetime
from textwrap import dedent
from selenium.webdriver.support.events import AbstractEventListener

HAR_CAPTURE_MODES = ('error', 'explicit', 'auto')


class MethodNotEnabledInCurrentMode(Exception):
    """
    An exception for when a method is called that should not be used
    in the current mode.
    """
    def __str__(self):
        return (
            "To manipulate the har on your own, please use @attr(har_mode='"
            "explicit') or BOK_CHOY_HAR_MODE='explicit'."
        )

class UnknownHarCaptureMode(Exception):
    """
    An exception for when the mode selected doesn't match any defined
    modes.
    """
    def __str__(self):
        return 'Expected one of: {}'.format(HAR_CAPTURE_MODES)


class HarListener(AbstractEventListener):
    """
    An object that can automatically track and save a HAR file from the
    selenium controlled browser.

    Usage:
        driver = EventFiringWebDriver(driver, HarListener(har_capturer))

    Args:
        har_capturer: An instance of HarCapturer.

    """
    def __init__(self, har_capturer, *args, **kwargs):  # pylint: disable=super-on-old-class
        super(HarListener, self).__init__(*args, **kwargs)
        self.har_capturer = har_capturer

    def before_navigate_to(self, url, driver):  # pylint: disable=missing-docstring
        if self.har_capturer.mode in ('auto', 'error'):
            self.har_capturer.add_page(driver, url, caller_mode=self.har_capturer.mode)

    def before_close(self, driver):  # pylint: disable=missing-docstring
        if self.har_capturer.mode in ('auto',):
            self.har_capturer.save_har(driver, caller_mode=self.har_capturer.mode)

    def before_quit(self, driver):  # pylint: disable=missing-docstring
        if self.har_capturer.mode in ('auto',):
            self.har_capturer.save_har(driver, caller_mode=self.har_capturer.mode)


class HarCapturer(object):
    """
    An object that can track and manipulate HAR files.

    Args:
        proxy: a browsermobproxy proxy instance.

    Keyword Args:
        har_base_name: A base for the har file names. The har filename may
            still have the datetime and 'cached' specifier appended to them.

        mode: 'auto', 'error', or 'explicit'. Although it is a kwarg, an
            UnknownHarCaptureMode exception will be raised if no mode is passed
            or if the mode doesn't match one of the following.

            * auto: automatically save a single har file for each test.
            * error: automatically save a single har file for each test only if
                it fails or errors.
            * explicit: interact explicitly with this object in order to capture
                and save a har file.
    """
    def __init__(self, *args, **kwargs):
        super(HarCapturer, self).__init__()

        # We need to access the proxy server in addition to the browser.
        self.proxy = args[0]
        self._har_base_name = kwargs.get('har_base_name', '')

        self.mode = kwargs.get('mode', None)

        if self.mode not in HAR_CAPTURE_MODES:
            raise UnknownHarCaptureMode

        # Vars for tracking state
        self._page_timings = []
        self._active_har = False
        self._with_cache = False

    def _validate_mode(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Raises MethodNotEnabledInCurrentMode if a user tries to interact
        with the har explicitly while in 'auto' or 'error' mode.
        """
        caller_mode = kwargs.get('caller_mode', 'explicit')
        if caller_mode != self.mode:
            raise MethodNotEnabledInCurrentMode

    def add_page(self, driver, page_name, *args, **kwargs):
        """
        Creates a new page within the har file. If no har file has been started
        since the last save, it will create one.

        Args:
            page_name: a string to be used as the page name in the har

        Returns:
            None
        """
        self._validate_mode(*args, **kwargs)

        if not self._active_har:
            # Start up a new HAR file
            self.proxy.new_har(
                ref=page_name,
                options={
                    'captureContent': True,
                    'captureHeaders': True,
                    'captureBinaryContent': True,
                }
            )

            self._page_timings = []
            self._active_har = True
        else:
            # Save the timings for the previous page before moving on to recording the new one.
            self._record_page_timings(driver)
            self.proxy.new_page(ref=page_name)

    def _record_page_timings(self, driver):
        """
        Saves recorded page timings to self.timings to be added to the har file
        on save.

        Returns:
            None
        """

        script = dedent("""
            var performance = window.performance || {};
            var timings = performance.timing || {};
            return timings;
        """)

        # Capture the timings from the browser via javascript
        timings = driver.execute_script(script)
        self._page_timings.append(timings)


    def har_name(self, name_override=None):
        """
        Returns the name to use for a saved artifacts.
        """

        if name_override:
            file_name = name_override

        else:
            file_name = "{}_{}".format(
                self._har_base_name,
                datetime.datetime.utcnow().isoformat()
            )

        if self._with_cache:
            file_name += '_cached'

        return file_name

    def save_har(self, driver, name_override=None, *args, **kwargs):
        """
        Save a HAR file.

        The location of the har file can be configured
        by the environment variable `BOK_CHOY_HAR_DIR`.  If not set,
        this defaults to the current working directory.

        Returns:
            None
        """
        self._validate_mode(*args, **kwargs)

        if self._active_har:
            # Record the most recent pages timings
            self._record_page_timings(driver)
            timings = self._page_timings

            # Get the har contents from the proxy
            har = self.proxy.har

            # Record the timings from the pages
            for index, _timing in enumerate(timings):
                nav_start = timings[index]['navigationStart']
                dom_content_loaded_event_end = timings[index]['domContentLoadedEventEnd']
                load_event_end = timings[index]['loadEventEnd']
                har['log']['pages'][index]['pageTimings']['onContentLoad'] = dom_content_loaded_event_end - nav_start
                har['log']['pages'][index]['pageTimings']['onLoad'] = load_event_end - nav_start

            har_file = os.path.join(
                os.environ.get('BOK_CHOY_HAR_DIR', ''),
                '{}.har'.format(self.har_name(name_override)))
            with open(har_file, 'w') as output_file:
                json.dump(har, output_file)
                output_file.close()

            # Set this to false so that a new har will be started if new_page is called again
            self._active_har = False
