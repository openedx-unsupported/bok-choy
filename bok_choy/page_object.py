"""
Base implementation of the Page Object pattern.
See https://code.google.com/p/selenium/wiki/PageObjects
"""
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import defaultdict, namedtuple
from functools import wraps
from contextlib import contextmanager
import json
import logging
import os
import socket
from textwrap import dedent
import urlparse

import requests
from selenium.common.exceptions import WebDriverException

from .query import BrowserQuery
from .promise import Promise, EmptyPromise, BrokenPromise


CUR_DIR = os.path.dirname(os.path.abspath(__file__))
AXS_FILE = os.path.join(os.path.split(CUR_DIR)[0], 'bok_choy/vendor/google/axs_testing.js')
AuditResults = namedtuple('AuditResults', 'errors, warnings')


class WrongPageError(Exception):
    """
    The page object reports that we're on the wrong page!
    """
    pass


class PageLoadError(Exception):
    """
    An error occurred while loading the page.
    """
    pass


class AccessibilityError(Exception):
    """
    The page violates one or more accessibility rules.
    """
    pass


def unguarded(method):
    """
    Mark a PageObject method as unguarded.

    Unguarded methods don't verify that the PageObject is
    on the current browser page before they execute

    Args:
        method (callable): The method to decorate.

    Returns:
        Decorated method
    """
    method._unguarded = True  # pylint: disable=protected-access
    return method


def pre_verify(method):
    """
    Decorator that calls self._verify_page() before executing the decorated method

    Args:
        method (callable): The method to decorate.

    Returns:
        Decorated method
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):  # pylint: disable=missing-docstring
        self._verify_page()  # pylint: disable=protected-access
        return method(self, *args, **kwargs)
    return wrapper


class _PageObjectMetaclass(ABCMeta):
    """
    Decorates any callable attributes of the class
    so that they call self._verify_page() before executing.

    Excludes any methods marked as unguarded with the @unguarded
    decorator, any methods starting with _, or in the list ALWAYS_UNGUARDED.
    """
    ALWAYS_UNGUARDED = ['url', 'is_browser_on_page']

    def __new__(mcs, cls_name, cls_bases, cls_attrs):
        for name, attr in cls_attrs.items():
            # Skip methods marked as unguarded
            if getattr(attr, '_unguarded', False) or name in mcs.ALWAYS_UNGUARDED:
                continue

            # Skip private methods
            if name.startswith('_'):
                continue

            # Skip class attributes that are classes themselves
            if isinstance(attr, type):
                continue

            is_property = isinstance(attr, property)

            # Skip non-callable attributes
            if not (callable(attr) or is_property):
                continue

            if is_property:
                # For properties, wrap each of the sub-methods separately
                property_methods = defaultdict(None)
                for fn_name in ('fdel', 'fset', 'fget'):
                    prop_fn = getattr(cls_attrs[name], fn_name, None)
                    if prop_fn is not None:
                        # Check for unguarded properties
                        if getattr(prop_fn, '_unguarded', False):
                            property_methods[fn_name] = prop_fn
                        else:
                            property_methods[fn_name] = pre_verify(prop_fn)
                cls_attrs[name] = property(**property_methods)
            else:
                cls_attrs[name] = pre_verify(attr)

        return super(_PageObjectMetaclass, mcs).__new__(mcs, cls_name, cls_bases, cls_attrs)


class PageObject(object):
    """
    Encapsulates user interactions with a specific part
    of a web application.

    The most important thing is this:
    Page objects encapsulate Selenium.

    If you find yourself writing CSS selectors in tests,
    manipulating forms, or otherwise interacting directly
    with the web UI, stop!

    Instead, put these in a :class:`PageObject` subclass :)

    PageObjects do their best to verify that they are only
    used when the browser is on a page containing the object.
    To do this, they will call :meth:`is_browser_on_page` before executing
    any of their methods, and raise a :class:`WrongPageError` if the
    browser isn't on the correct page.

    Generally, this is the right behavior. However, at times it
    will be useful to not verify the page before executing a method.
    In those cases, the method can be marked with the :func:`unguarded`
    decorator. Additionally, private methods (those beginning with `_`)
    are always unguarded.

    Class or instance properties are never guarded. However, methods
    marked with the :func:`property` are candidates for being guarded.
    To make them unguarded, you must mark the getter, setter, and deleter
    as :func:`unguarded` separately, and those decorators must be applied before
    the :func:`property` decorator.

    Correct::

        @property
        @unguarded
        def foo(self):
            return self._foo

    Incorrect::

        @unguarded
        @property
        def foo(self):
            return self._foo
    """

    __metaclass__ = _PageObjectMetaclass

    def __init__(self, browser):
        """
        Initialize the page object to use the specified browser instance.

        Args:
            browser (selenium.webdriver): The Selenium-controlled browser.

        Returns:
            PageObject
        """
        self.browser = browser
        flag = os.environ.get('VERIFY_ACCESSIBILITY', 'False')
        self.verify_accessibility = flag.lower() == 'true'

    @abstractmethod
    def is_browser_on_page(self):
        """
        Check that we are on the right page in the browser.
        The specific check will vary from page to page,
        but usually this amounts to checking the:

            1) browser URL
            2) page title
            3) page headings

        Returns:
            A `bool` indicating whether the browser is on the correct page.
        """
        return False

    @abstractproperty
    def url(self):
        """
        Return the URL of the page.  This may be dynamic,
        determined by configuration options passed to the
        page object's constructor.

        Some pages may not be directly accessible:
        perhaps the page object represents a "navigation"
        component that occurs on multiple pages.
        If this is the case, subclasses can return `None`
        to indicate that you can't directly visit the page object.
        """
        return None

    @unguarded
    def warning(self, msg):
        """
        Subclasses call this to indicate that something unexpected
        occurred while interacting with the page.

        Page objects themselves should never make assertions or
        raise exceptions, but they can issue warnings to make
        tests easier to debug.

        Args:
            msg (str): The message to log as a warning.

        Returns:
            None
        """
        log = logging.getLogger(self.__class__.__name__)
        log.warning(msg)

    @unguarded
    def visit(self):
        """
        Open the page containing this page object in the browser.

        Some page objects may not provide a URL, in which case
        a `NotImplementedError` will be raised.

        Raises:
            PageLoadError: The page did not load successfully.
            NotImplementedError: The page object does not provide a URL to visit.

        Returns:
            PageObject
        """
        if self.url is None:
            raise NotImplementedError("Page {} does not provide a URL to visit.".format(self))

        # Validate the URL
        if not self.validate_url(self.url):
            raise PageLoadError("Invalid URL: '{}'".format(self.url))

        # Visit the URL
        try:
            self.browser.get(self.url)
        except (WebDriverException, socket.gaierror):
            raise PageLoadError("Could not load page '{!r}' at URL '{}'".format(
                self, self.url
            ))

        # Give the browser enough time to get to the page, then return the page object
        # so that the caller can chain the call with an action:
        # Example: FooPage.visit().do_something()
        #
        # A BrokenPromise will be raised if the page object's is_browser_on_page method
        # does not return True before timing out.
        try:
            return self.wait_for_page()
        except BrokenPromise:
            raise PageLoadError("Timed out waiting to load page '{!r}' at URL '{}'".format(
                self, self.url
            ))

    @classmethod
    @unguarded
    def validate_url(cls, url):
        """
        Return a boolean indicating whether the URL has a protocol and hostname.
        If a port is specified, ensure it is an integer.

        Arguments:
            url (str): The URL to check.

        Returns:
            Boolean indicating whether the URL has a protocol and hostname.
        """
        result = urlparse.urlsplit(url)

        # Check that we have a protocol and hostname
        if not result.scheme or not result.netloc:
            return False

        # Check that the port is an integer
        try:
            if result.port is not None:
                int(result.port)
            elif result.netloc.endswith(':'):
                # Valid URLs do not end with colons.
                return False
        except ValueError:
            return False
        else:
            return True

    def _verify_page(self):
        """
        Ask the page object if we're on the right page;
        if not, raise a `WrongPageError`.
        """
        if not self.is_browser_on_page():
            msg = "Not on the correct page to use '{!r}' at URL '{}'".format(
                self, self.url
            )
            raise WrongPageError(msg)

    @unguarded
    def wait_for_page(self, timeout=30):
        """
        Block until the page loads, then returns the page.
        Useful for ensuring that we navigate successfully to a particular page.

        Keyword Args:
            timeout (int): The number of seconds to wait for the page before timing out with an exception.

        Raises:
            BrokenPromise: The timeout is exceeded without the page loading successfully.
        """
        result = Promise(
            lambda: (self.is_browser_on_page(), self), "loaded page {!r}".format(self),
            timeout=timeout
        ).fulfill()

        if self.verify_accessibility:
            self._check_for_accessibility_errors()

        return result

    @unguarded
    def q(self, **kwargs):  # pylint: disable=invalid-name
        """
        Construct a query on the browser.

        Example usages:

        .. code:: python

            self.q(css="div.foo").first.click()
            self.q(xpath="/foo/bar").text

        Keyword Args:
            css: A CSS selector.
            xpath: An XPath selector.

        Returns:
            BrowserQuery
        """
        return BrowserQuery(self.browser, **kwargs)

    @contextmanager
    def handle_alert(self, confirm=True):
        """
        Context manager that ensures alerts are dismissed.

        Example usage:

        .. code:: python

            with self.handle_alert():
                self.q(css='input.submit-button').first.click()

        Keyword Args:
            confirm (bool): Whether to confirm or cancel the alert.

        Returns:
            None
        """

        # Before executing the `with` block, stub the confirm/alert functions
        script = dedent("""
            window.confirm = function() {{ return {0}; }};
            window.alert = function() {{ return; }};
        """.format("true" if confirm else "false")).strip()
        self.browser.execute_script(script)

        # Execute the `with` block
        yield

    @unguarded
    def wait_for_ajax(self):
        """
        Wait for all ajax requests to finish.

        Example usage:

        .. code:: python

            self.q(css='input#email').fill("foo")
            self.wait_for_ajax()

        Returns:
            None
        """
        def _is_ajax_finished():
            """
            Check if all the ajax calls on the current page have completed.
            """
            return self.browser.execute_script("return jQuery.active") == 0

        EmptyPromise(_is_ajax_finished, "Finished waiting for ajax requests.").fulfill()

    @unguarded
    def wait_for(self, promise_check_func, description, result=False, timeout=60):
        """
        Calls the method provided as an argument until the Promise satisfied or BrokenPromise

        Arguments:
            promise_check_func (callable):
                * If `result` is False Then
                    Function that accepts no arguments and returns a boolean indicating whether the promise is fulfilled
                * If `result` is True Then
                    Function that accepts no arguments and returns a `(is_satisfied, result)` tuple,
                    where `is_satisfied` is a boolean indicating whether the promise was satisfied, and `result`
                    is a value to return from the fulfilled `Promise`
            description (str): Description of the Promise, used in log messages
            result (bool): Indicates whether we need result
            timeout (float): Maximum number of seconds to wait for the Promise to be satisfied before timing out

        Raises:
            BrokenPromise: the `Promise` was not satisfied

        """
        if result:
            return Promise(promise_check_func, description, timeout=timeout).fulfill()
        else:
            return EmptyPromise(promise_check_func, description, timeout=timeout).fulfill()

    @unguarded
    def wait_for_element_presence(self, element_selector, description, timeout=60):
        """
        Waits for element specified by `element_selector` to be present in DOM.

        Example usage:

        .. code:: python

            self.wait_for_element_presence('.submit', 'Submit Button is Present')

        Arguments:
            element_selector (str): css selector of the element.
            description (str): Description of the Promise, used in log messages.
            timeout (float): Maximum number of seconds to wait for the Promise to be satisfied before timing out

        """
        self.wait_for(lambda: self.q(css=element_selector).present, description=description, timeout=timeout)

    @unguarded
    def wait_for_element_absence(self, element_selector, description, timeout=60):
        """
        Waits for element specified by `element_selector` until it disappears from DOM.

        Example usage:

        .. code:: python

            self.wait_for_element_absence('.submit', 'Submit Button is not Present')

        Arguments:
            element_selector (str): css selector of the element.
            description (str): Description of the Promise, used in log messages.
            timeout (float): Maximum number of seconds to wait for the Promise to be satisfied before timing out

        """
        self.wait_for(lambda: not self.q(css=element_selector).present, description=description, timeout=timeout)

    @unguarded
    def wait_for_element_visibility(self, element_selector, description, timeout=60):
        """
        Waits for element specified by `element_selector` until it is displayed on web page.

        Example usage:

        .. code:: python

            self.wait_for_element_visibility('.submit', 'Submit Button is Visible')

        Arguments:
            element_selector (str): css selector of the element.
            description (str): Description of the Promise, used in log messages.
            timeout (float): Maximum number of seconds to wait for the Promise to be satisfied before timing out

        """
        self.wait_for(lambda: self.q(css=element_selector).visible, description=description, timeout=timeout)

    @unguarded
    def wait_for_element_invisibility(self, element_selector, description, timeout=60):
        """
        Waits for element specified by `element_selector` until it disappears from the web page.

        Example usage:

        .. code:: python

            self.wait_for_element_invisibility('.submit', 'Submit Button Disappeared')

        Arguments:
            element_selector (str): css selector of the element.
            description (str): Description of the Promise, used in log messages.
            timeout (float): Maximum number of seconds to wait for the Promise to be satisfied before timing out

        """
        self.wait_for(lambda: not self.q(css=element_selector).visible, description=description, timeout=timeout)

    def axs_audit_rules_to_run(self):
        """
        List of rules to check for accessibility errors on the page.
        See https://github.com/GoogleChrome/accessibility-developer-tools/tree/master/src/audits

        E.g. return ['badAriaAttributeValue']
        An empty list means to check for all available rules.
        None means that no audit should be done for this page.
        """
        return []

    def axs_audit_rules_to_ignore(self):
        """
        List of rules to ignore for accessibility errors on the page.
        See https://github.com/GoogleChrome/accessibility-developer-tools/tree/master/src/audits

        E.g. return ['badAriaAttributeValue']
        An empty list means to run rules as defined by axs_audit_rules_to_run.
        Otherwise, if rules are listed here, they will be ignored even if
        they are specified in axs_audit_rules_to_run.
        """
        return []

    def axs_scope(self):
        """
        The "start point" for the audit: the element which contains the portion of
        the page which should be audited.

        E.g. return 'document.querySelector("div#foo")'
        Defaults to using the document as the scope.
        """
        return 'null'

    def do_axs_audit(self):
        """
        Use Google's Accessibility Developer Tools to audit the
        page for accessibility problems.

        See https://github.com/GoogleChrome/accessibility-developer-tools

        Since this needs to inject JavaScript into the browser page, the only
        known way to do this is to use PhantomJS as your browser.

        Raises:
            NotImplementedError if you are not using PhantomJS
            RuntimeError if there was a problem with the injected JS or getting the report

        Returns:
            A list (one for each browser session) of namedtuples with 'errors' and 'warnings'
            fields whose values are the errors and warnings returned from the audit.

            None if the page object has no rules defined to check.
        """
        if self.browser.name != 'phantomjs':
            msg = 'Accessibility auditing is only supported with PhantomJS as the browser.'
            raise NotImplementedError(msg)

        if not os.path.isfile(AXS_FILE):
            msg = 'Could not find the accessibility tools JS file: {}'.format(AXS_FILE)
            raise RuntimeError(msg)

        rules = self.axs_audit_rules_to_run()
        if rules is None:
            msg = 'No accessibility rules were specified to check for this page: {}'.format(self)
            self.warning(msg)
            return None

        # The ghostdriver URL will be something like this: 'http://localhost:33225/wd/hub'
        ghostdriver_url = self.browser.service.service_url

        # Get the session_id from ghostdriver so that we can inject JS into the page.
        resp = requests.get('{}/sessions'.format(ghostdriver_url))
        sessions = resp.json()

        # report is the list that is returned, with one item for each browser session
        report = []

        for session in sessions.get('value'):
            session_id = session.get('id')

            # First make sure you can successfully inject the JS on the page
            script = dedent("""
                return this.injectJs("{file}");
            """.format(file=AXS_FILE))

            payload = {"script": script, "args": []}
            resp = requests.post('{}/session/{}/phantom/execute'.format(
                ghostdriver_url, session_id), data=json.dumps(payload))

            result = resp.json().get('value')
            if result is False:
                msg = '{msg} \nScript:{script} \nResponse:{response}'.format(
                    msg='Failure injecting the Accessibility Audit JS on the page.',
                    script=script,
                    response=resp.text)
                raise RuntimeError(msg)

            # This line will only be included in the script if rules to check on this page
            # are specified, as the default behavior of the js is to run all rules.
            if len(rules) > 0:
                rules_config = "auditConfig.auditRulesToRun = {rules};".format(
                    rules=rules)
            else:
                rules_config = ""

            ignored_rules = self.axs_audit_rules_to_ignore()
            if ignored_rules:
                rules_config += (
                    "\nauditConfig.auditRulesToIgnore = {rules};".format(
                        rules=ignored_rules
                    )
                )

            script = dedent("""
                return this.evaluate(function() {{
                  var auditConfig = new axs.AuditConfiguration();
                  {rules_config}
                  auditConfig.scope = {scope};
                  var run_results = axs.Audit.run(auditConfig);
                  var audit_results = axs.Audit.auditResults(run_results)
                  return audit_results;
                }});
            """.format(rules_config=rules_config, scope=self.axs_scope()))

            payload = {"script": script, "args": []}
            resp = requests.post('{}/session/{}/phantom/execute'.format(
                ghostdriver_url, session_id), data=json.dumps(payload))

            result = resp.json().get('value')
            if result is None:
                msg = '{} {} \nScript:{} \nResponse:{}'.format(
                    'No results were returned by the audit report.',
                    'Perhaps there was a problem with the rules or scope defined for this page.',
                    script,
                    resp.text)
                raise RuntimeError(msg)

            # audit_results is report of accessibility errors for that session
            audit_results = AuditResults(errors=result.get('errors_'), warnings=result.get('warnings_'))
            report.append(audit_results)

        return report

    def _check_for_accessibility_errors(self):
        """
        Parse the results of an axs_audit and raise a single exception
        if there are violations.

        Note that an error is only raised on errors, not on warnings.

        Returns:
            None

        Raises:
            AccessibilityError
        """
        errors = []
        audit = self.do_axs_audit()
        for session_result in audit:
            if session_result:
                if len(session_result.errors) > 0:
                    errors.extend(session_result.errors)

        num_errors = len(errors)

        if num_errors > 0:
            msg = "URL '{}' has {} errors: {}".format(self.url, num_errors, ", ".join(errors))
            raise AccessibilityError(msg)
