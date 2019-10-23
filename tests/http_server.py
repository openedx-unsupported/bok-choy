"""
An HTTP service for serving pages for tests, with
a configurable delay that can be passed as a
query parameter in a GET request.
"""
from __future__ import absolute_import, print_function

import os
from time import sleep
from six.moves.SimpleHTTPServer import SimpleHTTPRequestHandler
from six.moves.urllib_parse import urlparse, parse_qs  # pylint: disable=wrong-import-order
from six.moves import BaseHTTPServer


class DelayedRequestHandler(SimpleHTTPRequestHandler):
    """
    Request handler with a configurable delay for testing
    """
    def __init__(self, *args, **kwargs):
        SimpleHTTPRequestHandler.__init__(self, *args, **kwargs)
        self.path = None

    def do_GET(self):  # pylint: disable=invalid-name
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
    """
    Start an HTTP server on the port specified in the SERVER_PORT
    environment variable.  Serves the files located under ``tests/site``.
    """
    handler_class = DelayedRequestHandler
    handler_class.protocol_version = "HTTP/1.0"
    server_class = BaseHTTPServer.HTTPServer
    port = int(os.environ['SERVER_PORT'])
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)

    address = httpd.socket.getsockname()
    print("Serving HTTP on", address[0], "port", address[1], "...")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
