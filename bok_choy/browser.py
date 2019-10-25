"""
Use environment variables to configure Selenium remote WebDriver.
For use with SauceLabs (via SauceConnect) or local browsers.
"""
from __future__ import absolute_import, print_function

import errno
import logging
import os
import socket
from json import dumps
from shutil import copyfile

try:
    from needle.driver import (
        NeedleChrome as Chrome,
        NeedleFirefox as Firefox,
        NeedleIe as Ie,
        NeedleOpera as Opera,
        NeedlePhantomJS as PhantomJS,
        NeedleSafari as Safari
    )
except ImportError:
    from selenium.webdriver import Chrome, Firefox, Ie, Opera, PhantomJS, Safari
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options as FirefoxOptions

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
    'SELENIUM_INSECURE_CERTS',
]


BROWSERS = {
    'chrome': Chrome,
    'firefox': Firefox,
    'internet explorer': Ie,
    'opera': Opera,
    'phantomjs': PhantomJS,
    'safari': Safari,
}

FIREFOX_PROFILE_ENV_VAR = 'FIREFOX_PROFILE_PATH'

# A list of functions accepting one FirefoxProfile argument
FIREFOX_PROFILE_CUSTOMIZERS = []


class BrowserConfigError(Exception):

    """
    Misconfiguration error in the environment variables.
    """
    pass


def save_source(driver, name):
    """
    Save the rendered HTML of the browser.

    The location of the source can be configured
    by the environment variable `SAVED_SOURCE_DIR`.  If not set,
    this defaults to the current working directory.

    Args:
        driver (selenium.webdriver): The Selenium-controlled browser.
        name (str): A name to use in the output file name.
            Note that ".html" is appended automatically

    Returns:
        None
    """
    source = driver.page_source
    saved_source_dir = os.environ.get('SAVED_SOURCE_DIR')
    if not saved_source_dir:
        LOGGER.warning('The SAVED_SOURCE_DIR environment variable was not set; not saving page source')
        return
    file_name = os.path.join(saved_source_dir,
                             '{name}.html'.format(name=name))

    try:
        if not os.path.exists(saved_source_dir):
            os.makedirs(saved_source_dir)
        with open(file_name, 'wb') as output_file:
            output_file.write(source.encode('utf-8'))
    except Exception:  # pylint: disable=broad-except
        msg = u"Could not save the browser page source to {}.".format(file_name)
        LOGGER.warning(msg)


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
        screenshot_dir = os.environ.get('SCREENSHOT_DIR')
        if not screenshot_dir:
            LOGGER.warning('The SCREENSHOT_DIR environment variable was not set; not saving a screenshot')
            return
        elif not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
        image_name = os.path.join(screenshot_dir, name + '.png')
        driver.save_screenshot(image_name)

    else:
        msg = (
            u"Browser does not support screenshots. "
            u"Could not save screenshot '{name}'"
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
    browser_name = os.environ.get('SELENIUM_BROWSER', 'firefox')
    log_dir = os.environ.get('SELENIUM_DRIVER_LOG_DIR')
    if not log_dir:
        LOGGER.warning('The SELENIUM_DRIVER_LOG_DIR environment variable was not set; not saving logs')
        return
    elif not os.path.exists(log_dir):
        os.makedirs(log_dir)
    if browser_name == 'firefox':
        # Firefox doesn't yet provide logs to Selenium, but does log to a separate file
        # https://github.com/mozilla/geckodriver/issues/284
        # https://firefox-source-docs.mozilla.org/testing/geckodriver/geckodriver/TraceLogs.html
        log_path = os.path.join(os.getcwd(), 'geckodriver.log')
        if os.path.exists(log_path):
            dest_path = os.path.join(log_dir, '{}_geckodriver.log'.format(prefix))
            copyfile(log_path, dest_path)
        return

    log_types = driver.log_types
    for log_type in log_types:
        try:
            log = driver.get_log(log_type)
            file_name = os.path.join(
                log_dir, '{}_{}.log'.format(prefix, log_type)
            )
            with open(file_name, 'w') as output_file:
                for line in log:
                    output_file.write("{}{}".format(dumps(line), '\n'))
        except:  # pylint: disable=bare-except
            msg = (
                u"Could not save browser log of type '{log_type}'. "
                u"It may be that the browser does not support it."
            ).format(log_type=log_type)

            LOGGER.warning(msg, exc_info=True)


def browser(tags=None, proxy=None, other_caps=None):
    """
    Interpret environment variables to configure Selenium.
    Performs validation, logging, and sensible defaults.

    There are three cases:

    1. Local browsers: If the proper environment variables are not all set for the second case,
        then we use a local browser.

        * The environment variable `SELENIUM_BROWSER` can be set to specify which local browser to use. The default is \
          Firefox.
        * Additionally, if a proxy instance is passed and the browser choice is either Chrome or Firefox, then the \
          browser will be initialized with the proxy server set.
        * The environment variable `SELENIUM_FIREFOX_PATH` can be used for specifying a path to the Firefox binary. \
          Default behavior is to use the system location.
        * The environment variable `FIREFOX_PROFILE_PATH` can be used for specifying a path to the Firefox profile. \
          Default behavior is to use a barebones default profile with a few useful preferences set.

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
        other_caps (dict of str): Additional desired capabilities to provide to remote WebDriver instances. Note
        that these values will be overwritten by environment variables described above. This is only used for
        remote driver instances, where such info is usually used by services for additional configuration and
        metadata.

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

            # Load in user given desired caps but override with derived caps from above. This is to retain existing
            # behavior. Only for remote drivers, where various testing services use this info for configuration.
            if browser_class == webdriver.Remote:
                desired_caps = other_caps or {}
                desired_caps.update(browser_kwargs.get('desired_capabilities', {}))
                browser_kwargs['desired_capabilities'] = desired_caps

            return True, browser_class(*browser_args, **browser_kwargs)

        except (socket.error, WebDriverException) as err:
            msg = str(err)
            LOGGER.debug(u'Failed to instantiate browser: %s', msg)
            return False, None

    browser_instance = Promise(
        # There are cases where selenium takes 30s to return with a failure, so in order to try 3
        # times, we set a long timeout. If there is a hang on the first try, the timeout will
        # be enforced.
        browser_check_func, "Browser is instantiated successfully.", try_limit=3, timeout=95).fulfill()

    return browser_instance


def add_profile_customizer(func):
    """Add a new function that modifies the preferences of the firefox profile object it receives as an argument"""
    FIREFOX_PROFILE_CUSTOMIZERS.append(func)


def clear_profile_customizers():
    """Remove any previously-configured functions for customizing the firefox profile"""
    FIREFOX_PROFILE_CUSTOMIZERS[:] = []


def _firefox_profile():
    """Configure the Firefox profile, respecting FIREFOX_PROFILE_PATH if set"""
    profile_dir = os.environ.get(FIREFOX_PROFILE_ENV_VAR)

    if profile_dir:
        LOGGER.info(u"Using firefox profile: %s", profile_dir)
        try:
            firefox_profile = webdriver.FirefoxProfile(profile_dir)
        except OSError as err:
            if err.errno == errno.ENOENT:
                raise BrowserConfigError(
                    u"Firefox profile directory {env_var}={profile_dir} does not exist".format(
                        env_var=FIREFOX_PROFILE_ENV_VAR, profile_dir=profile_dir))
            elif err.errno == errno.EACCES:
                raise BrowserConfigError(
                    u"Firefox profile directory {env_var}={profile_dir} has incorrect permissions. It must be \
                    readable and executable.".format(env_var=FIREFOX_PROFILE_ENV_VAR, profile_dir=profile_dir))
            else:
                # Some other OSError:
                raise BrowserConfigError(
                    u"Problem with firefox profile directory {env_var}={profile_dir}: {msg}"
                    .format(env_var=FIREFOX_PROFILE_ENV_VAR, profile_dir=profile_dir, msg=str(err)))
    else:
        LOGGER.info("Using default firefox profile")
        firefox_profile = webdriver.FirefoxProfile()

        # Bypasses the security prompt displayed by the browser when it attempts to
        # access a media device (e.g., a webcam)
        firefox_profile.set_preference('media.navigator.permission.disabled', True)

        # Disable the initial url fetch to 'learn more' from mozilla (so you don't have to
        # be online to run bok-choy on firefox)
        firefox_profile.set_preference('browser.startup.homepage', 'about:blank')
        firefox_profile.set_preference('startup.homepage_welcome_url', 'about:blank')
        firefox_profile.set_preference('startup.homepage_welcome_url.additional', 'about:blank')

        # Disable fetching an updated version of firefox
        firefox_profile.set_preference('app.update.enabled', False)

        # Disable plugin checking
        firefox_profile.set_preference('plugins.hide_infobar_for_outdated_plugin', True)

        # Disable health reporter
        firefox_profile.set_preference('datareporting.healthreport.service.enabled', False)

        # Disable all data upload (Telemetry and FHR)
        firefox_profile.set_preference('datareporting.policy.dataSubmissionEnabled', False)

        # Disable crash reporter
        firefox_profile.set_preference('toolkit.crashreporter.enabled', False)

        # Disable the JSON Viewer
        firefox_profile.set_preference('devtools.jsonview.enabled', False)

        # Grant OS focus to the launched browser so focus-related tests function correctly
        firefox_profile.set_preference('focusmanager.testmode', True)
    for function in FIREFOX_PROFILE_CUSTOMIZERS:
        function(firefox_profile)
    return firefox_profile


def _local_browser_class(browser_name):
    """
    Returns class, kwargs, and args needed to instantiate the local browser.
    """

    # Log name of local browser
    LOGGER.info(u"Using local browser: %s [Default is firefox]", browser_name)

    # Get class of local browser based on name
    browser_class = BROWSERS.get(browser_name)
    headless = os.environ.get('BOKCHOY_HEADLESS', 'false').lower() == 'true'
    if browser_class is None:
        raise BrowserConfigError(
            u"Invalid browser name {name}.  Options are: {options}".format(
                name=browser_name, options=", ".join(list(BROWSERS.keys()))))
    else:
        if browser_name == 'firefox':
            # Remove geckodriver log data from previous test cases
            log_path = os.path.join(os.getcwd(), 'geckodriver.log')
            if os.path.exists(log_path):
                os.remove(log_path)

            firefox_options = FirefoxOptions()
            firefox_options.log.level = 'trace'
            if headless:
                firefox_options.headless = True
            browser_args = []
            browser_kwargs = {
                'firefox_profile': _firefox_profile(),
                'options': firefox_options,
            }

            firefox_path = os.environ.get('SELENIUM_FIREFOX_PATH')
            firefox_log = os.environ.get('SELENIUM_FIREFOX_LOG')
            if firefox_path and firefox_log:
                browser_kwargs.update({
                    'firefox_binary': FirefoxBinary(
                        firefox_path=firefox_path, log_file=firefox_log)
                })
            elif firefox_path:
                browser_kwargs.update({
                    'firefox_binary': FirefoxBinary(firefox_path=firefox_path)
                })
            elif firefox_log:
                browser_kwargs.update({
                    'firefox_binary': FirefoxBinary(log_file=firefox_log)
                })

        elif browser_name == 'chrome':
            chrome_options = ChromeOptions()
            if headless:
                chrome_options.headless = True

            # Emulate webcam and microphone for testing purposes
            chrome_options.add_argument('--use-fake-device-for-media-stream')

            # Bypasses the security prompt displayed by the browser when it attempts to
            # access a media device (e.g., a webcam)
            chrome_options.add_argument('--use-fake-ui-for-media-stream')

            browser_args = []
            browser_kwargs = {
                'options': chrome_options,
            }
        else:
            browser_args, browser_kwargs = [], {}

        return browser_class, browser_args, browser_kwargs


def _remote_browser_class(env_vars, tags=None):
    """
    Returns class, kwargs, and args needed to instantiate the remote browser.
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
        LOGGER.info(u"Using SauceLabs: %s %s %s", caps['platform'], caps['browserName'], caps['version'])
    else:
        LOGGER.info(u"Using Remote Browser: %s", caps['browserName'])

    # Create and return a new Browser
    # We assume that the WebDriver end-point is running locally (e.g. using
    # SauceConnect)
    url = u"http://{0}:{1}/wd/hub".format(
        envs['SELENIUM_HOST'], envs['SELENIUM_PORT'])

    browser_args = []
    browser_kwargs = {
        'command_executor': url,
        'desired_capabilities': caps,
    }
    if caps['browserName'] == 'firefox':
        browser_kwargs['browser_profile'] = _firefox_profile()

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
    missing = [key for key, val in list(envs.items()) if val is None]
    if missing:
        msg = (
            u"These environment variables must be set: " + u", ".join(missing)
        )
        raise BrowserConfigError(msg)

    # Check that we support this browser
    if envs['SELENIUM_BROWSER'] not in BROWSERS:
        msg = u"Unsuppported browser: {0}".format(envs['SELENIUM_BROWSER'])
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
        'acceptInsecureCerts': bool(envs.get('SELENIUM_INSECURE_CERTS', False)),
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
