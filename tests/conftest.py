"""
pytest configuration and fixtures
"""

from __future__ import absolute_import, unicode_literals

from multiprocessing import Process
import os

import pytest

from .http_server import main as start_test_server

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def pytest_configure(config):  # pylint: disable=unused-argument
    """Set some environment variables to default values if absent"""
    if 'SCREENSHOT_DIR' not in os.environ:
        os.environ['SCREENSHOT_DIR'] = REPO_ROOT
    if 'SELENIUM_DRIVER_LOG_DIR' not in os.environ:
        os.environ['SELENIUM_DRIVER_LOG_DIR'] = REPO_ROOT
    if 'SERVER_PORT' not in os.environ and not hasattr(config, 'slaveinput'):
        config.server_ports = [str(port) for port in range(8020, 8040)]
        # In case we're only using one node
        os.environ['SERVER_PORT'] = '8020'


def pytest_configure_node(node):
    """Give each test node a distinct HTTP port to use"""
    os.environ['SERVER_PORT'] = node.config.server_ports.pop()


@pytest.fixture(scope='session')
def test_server(request):
    """Start server for test fixture site"""
    server = Process(target=start_test_server)

    def fin():
        """Stop the test server"""
        server.terminate()
    request.addfinalizer(fin)
    server.start()
