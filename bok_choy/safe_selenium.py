"""
Helper methods for writing robust Selenium tests.

This extra safety basically comes from:

    1) Explicitly waiting for DOM and JavaScript changes
       (NEVER waiting for a pre-determined amount of time)

    2) Retrying on common exceptions.

There is no magic bullet for writing robust Selenium tests,
but these methods provide a solid foundation.

Note that these methods should NOT themselves make assertions;
that's the job of the test.  They can, however, raise exceptions
if an operation cannot be performed.
"""
from textwrap import dedent
from contextlib import contextmanager
from .promise import Promise, fulfill_before, fulfill
from selenium.common.exceptions import WebDriverException, StaleElementReferenceException
from splinter.exceptions import ElementDoesNotExist


class KeepWaiting(Exception):
    """
    Dummy exception to indicate that a check function wants to continue waiting.
    """
    pass


RETRY_EXCEPTIONS = (
    WebDriverException, StaleElementReferenceException,
    ElementDoesNotExist, KeepWaiting
)


def no_error(func):
    """
    Decorator to create a `Promise` check function that is satisfied
    only when `func()` executes successfully.
    """
    def _inner():
        try:
            return_val = func()
        except RETRY_EXCEPTIONS:
            return (False, None)
        else:
            return (True, return_val)

    return _inner


class SafeSelenium(object):
    """
    Helper methods for robust Selenium tests.
    """

    browser = None

    def __init__(self, browser):
        """
        Initialize the helpers to use `browser` (a `splinter.Browser` instance).
        """
        self.browser = browser

    def is_css_present(self, css_selector):
        """
        Return a boolean indicating whether the css is present on the page.
        This is generally faster than retrieving all the elements.
        """
        return self.browser.is_element_present_by_css(css_selector)

    def css_map(self, css_selector, map_func):
        """
        Query information about elements that match `css_selector`.

        `map_func(el)` is a function that maps an element to a value.
        Returns a list of such mapped values, one for each element.
        """
        return fulfill(Promise(
            no_error(lambda: [map_func(el) for el in self._css_find(css_selector)]),
            "Get query elements that match '{0}'".format(css_selector),
            try_limit=5
        ))

    def css_count(self, css_selector):
        """
        Return the number of elements that match `css_selector`
        """
        return len(self._css_find(css_selector))

    def css_text(self, css_selector):
        return self.css_map(css_selector, lambda el: el.text)

    def css_value(self, css_selector):
        return self.css_map(css_selector, lambda el: el.value)

    def css_html(self, css_selector):
        return self.css_map(css_selector, lambda el: el.html)

    def css_click(self, css_selector):
        """
        Click the first element matched by `css_selector`
        (you can use CSS `:nth-of-type` if there is more than one match)
        """
        return fulfill(Promise(
            no_error(self._css_find(css_selector).first.click),
            "click '{0}'".format(css_selector), try_limit=5
        ))

    def css_check(self, css_selector):
        """
        Check the radio or checkbox matched by `css_selector`.
        """
        self.css_click(css_selector)
        return fulfill(Promise(
            no_error(lambda: self._css_find(css_selector).first.selected),
            "check '{0}'".format(css_selector)
        ))

    def select_option(self, name, value):
        """
        Set the option `name` to `value`.
        """
        select_css = "select[name='{0}']".format(name)
        css_selector = "{0} option[value='{1}']".format(select_css, value)

        self.css_click(css_selector)

        check_select_promise = Promise(
            no_error(lambda: self._css_find(select_css).first.value == value),
            "select '{0}' in '{1}'".format(value, name)
        )
        return fulfill(check_select_promise)

    def css_fill(self, css_selector, text):
        """
        Fill the first element matched by `css_selector` with `text`.
        (you can use CSS `:nth-of-type` if there is more than one match)
        """
        fill_promise = Promise(
            no_error(lambda: self._css_find(css_selector).first.fill(text)),
            "fill '{0}' with '{1}'".format(css_selector, text), try_limit=5
        )

        check_fill_promise = Promise(
            no_error(lambda: self._css_find(css_selector).first.value == text),
            "element '{0}' has value '{1}'".format(css_selector, text)
        )

        with fulfill_before(fill_promise):
            return fulfill(check_fill_promise)

    @contextmanager
    def handle_alert(self, confirm=True):
        """
        Ensure that alerts are dismissed in a way that works across browsers.

        `ok` indicates whether to confirm or cancel the alert.

        Example usage:

            with self.handle_alert():
                self.css_click('input.submit-button')
        """

        # Before executing the `with` block, stub the confirm/alert functions
        script = dedent("""
            window.confirm = function() {{ return {0}; }};
            window.alert = function() {{ return; }};
        """.format("true" if confirm else "false")).strip()
        self.browser.execute_script(script)

        # Execute the `with` block
        yield

    def disable_jquery_animations(self):
        """
        Disable JQuery animations on the page.  Any state changes
        will occur immediately to the final state.
        """
        self.browser.execute_script("jQuery.fx.off = true;")

    def _css_find(self, css_selector):
        """
        Return a list of elements on the page that match `css_selector`.
        """
        return self.browser.find_by_css(css_selector)
