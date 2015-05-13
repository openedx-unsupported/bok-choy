"""
Helpers for dealing with JavaScript synchronization issues.
"""
import functools
import json
from textwrap import dedent
from selenium.common.exceptions import TimeoutException, WebDriverException
from .promise import EmptyPromise


def js_defined(*js_vars):
    """
    Class decorator that ensures JavaScript variables are defined in the browser.

    This adds a `wait_for_js` method to the class, which will
    block until all the expected JavaScript variables are defined.

    Args:
        js_vars (list of str): List of JavaScript variable names to wait for.

    Returns:
        Decorated class
    """
    return _decorator('_js_vars', js_vars)


def requirejs(*modules):
    """
    Class decorator that ensures RequireJS modules are loaded in the browser.

    This adds a `wait_for_js` method to the class, which will
    block until all the expected RequireJS modules are loaded.

    Args:
        modules (list of str) List of RequireJS module names to wait for.

    Returns:
        Decorated class
    """
    return _decorator('_requirejs_deps', modules)


def wait_for_js(function):
    """
    Method decorator that waits for JavaScript dependencies before executing `function`.
    If the function is not a method, the decorator has no effect.

    Args:
        function (callable): Method to decorate.

    Returns:
        Decorated method
    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):  # pylint: disable=missing-docstring

        # If not a method, then just call the function
        if len(args) < 1:
            return function(*args, **kwargs)

        # Otherwise, retrieve `self` as the first arg
        else:
            self = args[0]

            # If the class has been decorated by one of the
            # JavaScript dependency decorators, it should have
            # a `wait_for_js` method
            if hasattr(self, 'wait_for_js'):
                self.wait_for_js()

            # Call the function
            return function(*args, **kwargs)

    return wrapper


def _decorator(store_name, store_values):
    """
    Return a class decorator that:

    1) Defines a new class method, `wait_for_js`
    2) Defines a new class list variable, `store_name` and adds
        `store_values` to the list.
    """
    def decorator(clz):  # pylint: disable=missing-docstring

        # Add a `wait_for_js` method to the class
        if not hasattr(clz, 'wait_for_js'):
            setattr(clz, 'wait_for_js', _wait_for_js)

        # Store the RequireJS module names in the class
        if not hasattr(clz, store_name):
            setattr(clz, store_name, set())

        getattr(clz, store_name).update(store_values)
        return clz

    return decorator


def _wait_for_js(self):
    """
    Class method added by the decorators to allow
    decorated classes to manually re-check JavaScript
    dependencies.

    Expect that `self` is a class that:
    1) Has been decorated with either `js_defined` or `requirejs`
    2) Has a `browser` property

    If either (1) or (2) is not satisfied, then do nothing.
    """

    # No Selenium browser available, so return without doing anything
    if not hasattr(self, 'browser'):
        return

    # pylint: disable=protected-access
    # Wait for JavaScript variables to be defined
    if hasattr(self, '_js_vars') and self._js_vars:
        EmptyPromise(
            lambda: _are_js_vars_defined(self.browser, self._js_vars),
            "JavaScript variables defined: {0}".format(", ".join(self._js_vars))
        ).fulfill()

    # Wait for RequireJS dependencies to load
    if hasattr(self, '_requirejs_deps') and self._requirejs_deps:
        EmptyPromise(
            lambda: _are_requirejs_deps_loaded(self.browser, self._requirejs_deps),
            "RequireJS dependencies loaded: {0}".format(", ".join(self._requirejs_deps)),
            try_limit=5
        ).fulfill()


def _are_js_vars_defined(browser, js_vars):
    """
    Return a boolean indicating whether all the JavaScript
    variables `js_vars` are defined on the current page.

    `browser` is a Selenium webdriver instance.
    """
    # This script will evaluate to True iff all of
    # the required vars are defined.
    script = " && ".join([
        "!(typeof {0} === 'undefined')".format(var)
        for var in js_vars
    ])

    try:
        return browser.execute_script("return {}".format(script))
    except WebDriverException as exc:
        if "is not defined" in exc.msg or "is undefined" in exc.msg:
            return False
        else:
            raise


def _are_requirejs_deps_loaded(browser, deps):
    """
    Return a boolean indicating whether all the RequireJS
    dependencies `deps` have loaded on the current page.

    `browser` is a WebDriver instance.
    """

    # This is a little complicated
    #
    # We're going to use `execute_async_script` to give control to
    # the browser.  The browser indicates that it wants to return
    # control to us by calling `callback`, which is the last item
    # in the global `arguments` array.
    #
    # We install a RequireJS module with the dependencies we want
    # to ensure are loaded.  When our module loads, we return
    # control to the test suite.
    script = dedent("""
        // Retrieve the callback function used to return control to the test suite
        var callback = arguments[arguments.length - 1];

        // If RequireJS isn't defined, then return immediately
        if (!window.require) {{
            callback("RequireJS not defined");
        }}

        // Otherwise, install a RequireJS module that depends on the modules
        // we're waiting for.
        else {{

            // Catch errors reported by RequireJS
            requirejs.onError = callback;

            // Install our module
            require({deps}, function() {{
                callback('Success');
            }});
        }}
    """).format(deps=json.dumps(list(deps)))

    # Set a timeout to ensure we get control back
    browser.set_script_timeout(30)

    # Give control to the browser
    # `result` will be the argument passed to the callback function
    try:
        result = browser.execute_async_script(script)
        return result == 'Success'

    except TimeoutException:
        return False
