"""
Base class for checking network performance of a web application.
"""
import functools
import os
import json
from web_app_test import WebAppTest
from .browser import browser
from browsermobproxy import Server
from textwrap import dedent


class WebAppPerfReport(WebAppTest):
    """
    Base class for generating reports for a web application page performance.

    This is a subclass of WebAppTest that allows you to interact with PageObjects
    while recording network traffic to har files.  You can write and run scenarios
    as tests (with assertions) if desired, but there are a few additional steps needed
    to produce the network timing reports.

    1. Indicate when you are about to navigate to a new page with the `new_page`
        method. Be sure to do this before going to the first page you want to record.
    2. Save the currently recording har with the `save_har` method.

    Example::

        class MyPerformanceTestClass(WebAppPerfReport):

            test_foo(self):
                foo_page = FooPage(self.browser)

                # Declare that you are going to foo_page.
                self.new_page('FooPage')

                # Then go to the foo_page.
                foo_page.visit()

                # Do some other interactions with the page if you want.
                # ...

                # Save the har file
                # This one will end up named 'FooPage.har'
                self.save_har('FooPage')

    Note: You can visit many pages in one har recording. You can also record many hars in one scenario.
    """

    def setUp(self):
        """
        Start the browser with a browsermob-proxy instance for use by the test.
        You *must* call this in the `setUp` method of any subclasses before using the browser!

        Returns:
            None
        """

        try:
            # Start server proxy
            server = Server('browsermob-proxy')
            server.start()
            self.proxy = server.create_proxy()
            proxy_host = os.environ.get('BROWSERMOB_PROXY_HOST', '127.0.0.1')
            self.proxy.remap_hosts('localhost', proxy_host)
        except:
            self.skipTest('Skipping: could not start server with browsermob-proxy.')

        # parent's setUp
        super(WebAppPerfReport, self).setUp()

        # Initialize vars
        self._page_timings = []
        self._active_har = False
        self._with_cache = False

        # Add one more cleanup for the server
        self.addCleanup(server.stop)
        
    def new_page(self, page_name):
        """
        Creates a new page within the har file. If no har file has been started 
        since the last save, it will create one.

        Args:
            page_name: a string to be used as the page name in the har
            
        Returns:
            None
        """
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
            self._record_page_timings()
            self.proxy.new_page(ref=page_name)

    def _record_page_timings(self):
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
        timings = self.browser.execute_script(script)
        self._page_timings.append(timings)

    def save_har(self, har_name=None):
        """
        Save a HAR file.

        The location of the har file can be configured
        by the environment variable `HAR_DIR`.  If not set,
        this defaults to the current working directory.

        Args:
            har_name (optional): title for the har file

        Returns:
            None
        """
        if not har_name:
            har_name = "{}_{}".format(self.id(), self.unique_id)
        if self._with_cache:
            har_name += '_cached'

        # Record the most recent pages timings
        self._record_page_timings()
        timings = self._page_timings

        # Get the har contents from the proxy
        har = self.proxy.har

        # Record the timings from the pages
        for index, timing in enumerate(timings):
            har['log']['pages'][index]['pageTimings']['onContentLoad'] = (timings[index]['domContentLoadedEventEnd'] - timings[index]['navigationStart'])
            har['log']['pages'][index]['pageTimings']['onLoad'] = (timings[index]['loadEventEnd'] - timings[index]['navigationStart'])

        har_file = os.path.join(os.environ.get('HAR_DIR', ''), '{}.har'.format(har_name))
        with open(har_file, 'w') as output_file:
            json.dump(har, output_file)

        # Set this to false so that a new har will be started if new_page is called again
        self._active_har = False


def with_cache(function):
    """
    A decorator to be used on a test case of a WebAppPerfReport test class to run it twice.

    This will produce two sets of har files; one for each time the scenario is executed. The
    second set of har files saved will have '_cached' appended to the file name to indicate that
    there may have been some resources cached prior to execution. The resources that may be in
    the cache will have come from the first time the scenario was run.

    Args:
        function (callable): The function to decorate. It should be a method of WebAppPerfReport.

    Returns:
        Decorated method
    """

    @functools.wraps(function)
    def wrapper(self, *args, **kwargs):
        """
        Runs the test case twice. The first time, there will be an empty cache. The second
        time, the cache will contain anything stored on the first call.
        """
        # Run once in a new browser instance.
        function(self, *args, **kwargs)

        # Run the whole thing again in the same browser instance.
        self._with_cache = True
        function(self, *args, **kwargs)

    return wrapper
