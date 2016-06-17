"""
An HTTP service for serving pages for tests, with
a configurable delay that can be passed as a
query parameter in a GET request.
"""

import os
import sys
from time import sleep
import six
from six.moves import BaseHTTPServer
from six.moves.SimpleHTTPServer import SimpleHTTPRequestHandler
from six.moves.urllib_parse import urlparse, parse_qs


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
    handler_class = DelayedRequestHandler
    handler_class.protocol_version = "HTTP/1.0"
    server_class = BaseHTTPServer.HTTPServer
    port = int(os.environ['SERVER_PORT'])
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)

    sa = httpd.socket.getsockname()
    print("Serving HTTP on", sa[0], "port", sa[1], "...")
    httpd.serve_forever()

if __name__ == "__main__":
    main()
