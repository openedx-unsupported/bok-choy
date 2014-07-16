"""
Base class for testing a web application.
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
    """

    def setUp(self):
        """
        Start the browser for use by the test.
        You *must* call this in the `setUp` method of any subclasses before using the browser!

        Returns:
            None
        """

        server = Server('browsermob-proxy')
        server.start()
        self.proxy = server.create_proxy()

        self.har_name = self.id()
        self.page_timings = []
        self.active_har = False
        self.har_count = 0

        # If using SauceLabs, tag the job with test info
        tags = [self.id()]

        # This will start the browser, so add a cleanup
        self.browser = browser(tags=tags, proxy=self.proxy)

        # Cleanups are executed in LIFO order.
        self.addCleanup(server.stop)
        self.addCleanup(self.browser.quit)
        
    def new_page(self, page_name):
        """
        Creates a new page within the har file. If no har file has been started 
        since the last save, it will create one.

        Args:
            page_name: a string to be used as the page name in the har
            
        Returns:
            None
        """
        if not self.active_har:
            # Start up a new HAR file
            self.proxy.new_har(
                ref=page_name, 
                options={
                    'captureContent': False,
                    'captureHeaders': True,
                    'captureBinaryContent': True,
                }
            )

            self.page_timings = []
            self.active_har = True
            self.har_count += 1
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
        self.page_timings.append(timings)

    def save_har(self):
        """
        Save a HAR file.

        The location of the har file can be configured
        by the environment variable `HAR_DIR`.  If not set,
        this defaults to the current working directory.

        Returns:
            None
        """
        # Record the most recent pages timings
        self._record_page_timings()
        timings = self.page_timings

        # Get the har contents from the proxy
        har = self.proxy.har

        # Record the timings from the pages
        for i in range(0, len(timings)):
            har['log']['pages'][i]['pageTimings']['onContentLoad'] = (timings[i]['domContentLoadedEventEnd'] - timings[i]['navigationStart'])
            har['log']['pages'][i]['pageTimings']['onLoad'] = (timings[i]['loadEventEnd'] - timings[i]['navigationStart'])

        har_file = os.path.join(os.environ.get('HAR_DIR', ''), '{}_{}.har'.format(self.har_name, self.har_count))
        with open(har_file, 'w') as output_file:
            json.dump(har, output_file)

        # Set this to false so that a new har will be started if new_page is called again
        self.active_har = False


def with_cache(function):
    """
    A decorator to be used on a test case of a WebAppPerfReport test class to run it twice.
    """

    @functools.wraps(function)
    def wrapper(self, *args, **kwargs):
        """
        Runs the test case twice. The first time, there will be an empty cache. The second
        time, the cache will contain anything stored on the first call.
        """
        # Check that self is a WebAppPerfReport instance.
        try: 
            base_classes = [base.__name__ for base in self.__class__.__bases__]
            if "WebAppPerfReport" not in base_classes: 
                raise
        except:
            raise Exception("Function must be a method of WebAppPerfReport.")

        # Run once in a new browser instance.
        function(self, *args, **kwargs)

        # Update this so that the new har files will indicate that there was cached data.
        self.har_name += '_cached'

        # run the whole thing again in the same browser instance.
        function(self, *args, **kwargs)

    return wrapper
