from __future__ import unicode_literals

from multiprocessing import Process
import os

import pytest

from .http_server import main as start_test_server

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def pytest_configure(config):
    """Set some environment variables to default values if absent"""
    if 'SCREENSHOT_DIR' not in os.environ:
        os.environ['SCREENSHOT_DIR'] = REPO_ROOT
    if 'SELENIUM_DRIVER_LOG_DIR' not in os.environ:
        os.environ['SELENIUM_DRIVER_LOG_DIR'] = REPO_ROOT
    if 'SERVER_PORT' not in os.environ:
        os.environ['SERVER_PORT'] = '8005'


@pytest.fixture(scope='session')
def test_server(request):
    """Start server for test fixture site"""
    server = Process(target=start_test_server)

    def fin():
        server.terminate()
    request.addfinalizer(fin)
    server.start()
