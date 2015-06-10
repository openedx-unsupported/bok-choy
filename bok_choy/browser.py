"""
Use environment variables to configure Selenium remote WebDriver.
For use with SauceLabs (via SauceConnect) or local browsers.
"""
import logging
from json import dumps
import os
import socket

from needle.driver import (NeedleFirefox, NeedleChrome, NeedleIe,
                           NeedleSafari, NeedlePhantomJS)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from bok_choy.promise import Promise

LOGGER = logging.getLogger(__name__)

REMOTE_ENV_VARS = [
    'SELENIUM_BROWSER',
    'SELENIUM_HOST',
    'SELENIUM_PORT',
]

SAUCE_ENV_VARS = REMOTE_ENV_VARS + [
    'SELENIUM_VERSION',
    'SELENIUM_PLATFORM',
    'SAUCE_USER_NAME',
    'SAUCE_API_KEY',
]


OPTIONAL_ENV_VARS = [
    'JOB_NAME',
    'BUILD_NUMBER',
]


BROWSERS = {
    'firefox': NeedleFirefox,
    'chrome': NeedleChrome,
    'internet explorer': NeedleIe,
    'safari': NeedleSafari,
    'phantomjs': NeedlePhantomJS
}


class BrowserConfigError(Exception):

    """
    Misconfiguration error in the environment variables.
    """
    pass


def save_screenshot(driver, name):
    """
    Save a screenshot of the browser.

    The location of the screenshot can be configured
    by the environment variable `SCREENSHOT_DIR`.  If not set,
    this defaults to the current working directory.

    Args:
        driver (selenium.webdriver): The Selenium-controlled browser.
        name (str): A name for the screenshot, which will be used in the output file name.

    Returns:
        None
    """
    if hasattr(driver, 'save_screenshot'):
        image_name = os.path.join(
            os.environ.get('SCREENSHOT_DIR', ''), name + '.png'
        )
        driver.save_screenshot(image_name)

    else:
        msg = (
            "Browser does not support screenshots. "
            "Could not save screenshot '{name}'"
        ).format(name=name)

        LOGGER.warning(msg)


def save_driver_logs(driver, prefix):
    """
    Save the selenium driver logs.

    The location of the driver log files can be configured
    by the environment variable `SELENIUM_DRIVER_LOG_DIR`.  If not set,
    this defaults to the current working directory.

    Args:
        driver (selenium.webdriver): The Selenium-controlled browser.
        prefix (str): A prefix which will be used in the output file names for the logs.

    Returns:
        None
    """
    log_types = ['browser', 'driver', 'client', 'server']
    for log_type in log_types:
        try:
            log = driver.get_log(log_type)
            file_name = os.path.join(
                os.environ.get('SELENIUM_DRIVER_LOG_DIR', ''), '{}_{}.log'.format(
                    prefix, log_type)
            )
            with open(file_name, 'w') as output_file:
                for line in log:
                    output_file.write("{}{}".format(dumps(line), '\n'))
        except:  # pylint: disable=bare-except
            msg = (
                "Could not save browser log of type '{log_type}'. "
                "It may be that the browser does not support it."
            ).format(log_type=log_type)

            LOGGER.warning(msg, exec_info=True)


def browser(tags=None, proxy=None):
    """
    Interpret environment variables to configure Selenium.
    Performs validation, logging, and sensible defaults.

    There are three cases:

    1. Local browsers: If the proper environment variables are not all set for the second case,
        then we use a local browser.  The environment variable `SELENIUM_BROWSER` can be set to
        specify which local browser to use, but the default is firefox.  Additionally, if a proxy
        instance is passed and the browser choice is either chrome or firefox, then the browser will
        be initialized with the proxy server set.

    2. Remote browser (not SauceLabs): Set all of the following environment variables, but not all of
        the ones needed for SauceLabs:

        * SELENIUM_BROWSER
        * SELENIUM_HOST
        * SELENIUM_PORT

    3. SauceLabs: Set all of the following environment variables:

        * SELENIUM_BROWSER
        * SELENIUM_VERSION
        * SELENIUM_PLATFORM
        * SELENIUM_HOST
        * SELENIUM_PORT
        * SAUCE_USER_NAME
        * SAUCE_API_KEY

    **NOTE:** these are the environment variables set by the SauceLabs
    Jenkins plugin.

    Optionally provide Jenkins info, used to identify jobs to Sauce:

        * JOB_NAME
        * BUILD_NUMBER

    `tags` is a list of string tags to apply to the SauceLabs
    job.  If not using SauceLabs, these will be ignored.

    Keyword Args:
        tags (list of str): Tags to apply to the SauceLabs job.  If not using SauceLabs, these will be ignored.
        proxy: A proxy instance.

    Returns:
        selenium.webdriver: The configured browser object used to drive tests

    Raises:
        BrowserConfigError: The environment variables are not correctly specified.
    """

    browser_name = os.environ.get('SELENIUM_BROWSER', 'firefox')

    def browser_check_func():
        """ Instantiate the browser and return the browser instance """
        # See https://openedx.atlassian.net/browse/TE-701
        try:
            # Get the class and kwargs required to instantiate the browser based on
            # whether we are using a local or remote one.
            if _use_remote_browser(SAUCE_ENV_VARS):
                browser_class, browser_args, browser_kwargs = _remote_browser_class(
                    SAUCE_ENV_VARS, tags)
            elif _use_remote_browser(REMOTE_ENV_VARS):
                browser_class, browser_args, browser_kwargs = _remote_browser_class(
                    REMOTE_ENV_VARS, tags)
            else:
                browser_class, browser_args, browser_kwargs = _local_browser_class(
                    browser_name)

            # If we are using a proxy, we need extra kwargs passed on intantiation.
            if proxy:
                browser_kwargs = _proxy_kwargs(browser_name, proxy, browser_kwargs)

            return True, browser_class(*browser_args, **browser_kwargs)

        except socket.error as err:
            LOGGER.debug('Failed to instantiate browser: ' + err.strerror)
            return False, None

    browser_instance = Promise(
        browser_check_func, "Browser is instantiated successfully.", timeout=30).fulfill()

    return browser_instance


def _local_browser_class(browser_name):
    """
    Returns class, kwargs, and args needed to instatiate the local browser.
    """

    # Log name of local browser
    LOGGER.info("Using local browser: %s [Default is firefox]", browser_name)

    # Get class of local browser based on name
    browser_class = BROWSERS.get(browser_name)
    if browser_class is None:
        raise BrowserConfigError(
            "Invalid browser name {name}.  Options are: {options}".format(
                name=browser_name, options=", ".join(BROWSERS.keys())))
    else:
        if browser_name == 'firefox':
            firefox_profile = webdriver.FirefoxProfile()

            # Bypasses the security prompt displayed by the browser when it attempts to
            # access a media device (e.g., a webcam)
            firefox_profile.set_preference('media.navigator.permission.disabled', True)

            browser_args = []
            browser_kwargs = {
                'firefox_profile': firefox_profile,
            }
        elif browser_name == 'chrome':
            chrome_options = Options()

            # Emulate webcam and microphone for testing purposes
            chrome_options.add_argument('--use-fake-device-for-media-stream')

            # Bypasses the security prompt displayed by the browser when it attempts to
            # access a media device (e.g., a webcam)
            chrome_options.add_argument('--use-fake-ui-for-media-stream')

            browser_args = []
            browser_kwargs = {
                'chrome_options': chrome_options,
            }
        else:
            browser_args, browser_kwargs = [], {}

        return browser_class, browser_args, browser_kwargs


def _remote_browser_class(env_vars, tags=None):
    """
    Returns class, kwargs, and args needed to instatiate the remote browser.
    """
    if tags is None:
        tags = []

    # Interpret the environment variables, raising an exception if they're
    # invalid
    envs = _required_envs(env_vars)
    envs.update(_optional_envs())

    # Turn the environment variables into a dictionary of desired capabilities
    caps = _capabilities_dict(envs, tags)

    if 'accessKey' in caps:
        LOGGER.info("Using SauceLabs: %s %s %s", caps['platform'], caps['browserName'], caps['version'])
    else:
        LOGGER.info("Using Remote Browser: %s", caps['browserName'])

    # Create and return a new Browser
    # We assume that the WebDriver end-point is running locally (e.g. using
    # SauceConnect)
    url = "http://{0}:{1}/wd/hub".format(
        envs['SELENIUM_HOST'], envs['SELENIUM_PORT'])

    browser_args = []
    browser_kwargs = {
        'command_executor': url,
        'desired_capabilities': caps,
    }

    return webdriver.Remote, browser_args, browser_kwargs


def _proxy_kwargs(browser_name, proxy, browser_kwargs={}):  # pylint: disable=dangerous-default-value
    """
    Determines the kwargs needed to set up a proxy based on the
    browser type.

    Returns: a dictionary of arguments needed to pass when
        instantiating the WebDriver instance.
    """

    proxy_dict = {
        "httpProxy": proxy.proxy,
        "proxyType": 'manual',
    }

    if browser_name == 'firefox' and 'desired_capabilities' not in browser_kwargs:
        # This one works for firefox locally
        wd_proxy = webdriver.common.proxy.Proxy(proxy_dict)
        browser_kwargs['proxy'] = wd_proxy
    else:
        # This one works with chrome, both locally and remote
        # This one works with firefox remote, but not locally
        if 'desired_capabilities' not in browser_kwargs:
            browser_kwargs['desired_capabilities'] = {}

        browser_kwargs['desired_capabilities']['proxy'] = proxy_dict

    return browser_kwargs


def _use_remote_browser(required_vars):
    """
    Returns a boolean indicating whether we should use a remote
    browser.  This means the user has made an attempt to set
    environment variables indicating they want to connect to SauceLabs
    or a remote browser.
    """
    return all([
        key in os.environ
        for key in required_vars
    ])


def _required_envs(env_vars):
    """
    Parse environment variables for required values,
    raising a `BrowserConfig` error if they are not found.

    Returns a `dict` of environment variables.
    """
    envs = {
        key: os.environ.get(key)
        for key in env_vars
    }

    # Check for missing keys
    missing = [key for key, val in envs.items() if val is None]
    if len(missing) > 0:
        msg = (
            "These environment variables must be set: " +
            ", ".join(missing)
        )
        raise BrowserConfigError(msg)

    # Check that we support this browser
    if envs['SELENIUM_BROWSER'] not in BROWSERS:
        msg = "Unsuppported browser: {0}".format(envs['SELENIUM_BROWSER'])
        raise BrowserConfigError(msg)

    return envs


def _optional_envs():
    """
    Parse environment variables for optional values,
    raising a `BrowserConfig` error if they are insufficiently specified.

    Returns a `dict` of environment variables.
    """
    envs = {
        key: os.environ.get(key)
        for key in OPTIONAL_ENV_VARS
        if key in os.environ
    }

    # If we're using Jenkins, check that we have all the required info
    if 'JOB_NAME' in envs and 'BUILD_NUMBER' not in envs:
        raise BrowserConfigError("Missing BUILD_NUMBER environment var")

    if 'BUILD_NUMBER' in envs and 'JOB_NAME' not in envs:
        raise BrowserConfigError("Missing JOB_NAME environment var")

    return envs


def _capabilities_dict(envs, tags):
    """
    Convert the dictionary of environment variables to
    a dictionary of desired capabilities to send to the
    Remote WebDriver.

    `tags` is a list of string tags to apply to the SauceLabs job.
    """
    capabilities = {
        'browserName': envs['SELENIUM_BROWSER'],
        'video-upload-on-pass': False,
        'sauce-advisor': False,
        'capture-html': True,
        'record-screenshots': True,
        'max-duration': 600,
        'public': 'public restricted',
        'tags': tags,
    }

    # Add SauceLabs specific environment vars if they are set.
    if _use_remote_browser(SAUCE_ENV_VARS):
        sauce_capabilities = {
            'platform': envs['SELENIUM_PLATFORM'],
            'version': envs['SELENIUM_VERSION'],
            'username': envs['SAUCE_USER_NAME'],
            'accessKey': envs['SAUCE_API_KEY'],
        }

        capabilities.update(sauce_capabilities)

    # Optional: Add in Jenkins-specific environment variables
    # to link Sauce output with the Jenkins job
    if 'JOB_NAME' in envs:
        jenkins_vars = {
            'build': envs['BUILD_NUMBER'],
            'name': envs['JOB_NAME'],
        }

        capabilities.update(jenkins_vars)

    return capabilities
