"""
An HTTP service for serving pages for tests, with
a configurable delay that can be passed as a
query parameter in a GET request.
"""

import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from urlparse import urlparse, parse_qs
from time import sleep


class DelayedRequestHandler(SimpleHTTPRequestHandler):
    """
    Request handler with a configurable delay for testing
    """
    def do_GET(self):
        """
        Check parameters to see if a delay was specified.
        If so then wait and then serve the GET request.
        """
        # Parse the url into components
        parsed_url = urlparse(self.path)

        # Determine if delay was passed as a parameter
        delay_time = parse_qs(parsed_url.query).get('delay')

        if delay_time:
            # Values are passed as a list of strings
            # so keep the first value and convert to a float.
            sleep(float(delay_time[0]))

        # Prepend "tests/site" to the path because that
        # is where the test files should be served from.
        self.path = "tests/site{}".format(self.path)

        return SimpleHTTPRequestHandler.do_GET(self)


def main():
    HANDLER_CLASS = DelayedRequestHandler
    SERVER_CLASS = BaseHTTPServer.HTTPServer
    BaseHTTPServer.test(HandlerClass=HANDLER_CLASS, ServerClass=SERVER_CLASS)

if __name__ == "__main__":
    main()
