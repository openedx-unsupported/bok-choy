"""
Page objects for interacting with the test site.
"""

import os
import time
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise, fulfill_before, fulfill_after, fulfill
from bok_choy.javascript import js_defined, requirejs, wait_for_js


class SitePage(PageObject):
    """
    Base class for all pages in the test site.
    """

    # Get the server port from the environment
    # (set by the test runner script)
    SERVER_PORT = os.environ.get("SERVER_PORT", 8003)

    # Subclasses override this
    NAME = None

    def is_browser_on_page(self):
        title = self.NAME.lower().replace('_', ' ')
        return title in self.browser.title.lower()

    def url(self, **kwargs):
        return "http://localhost:{0}/{1}".format(self.SERVER_PORT, self.NAME + ".html")

    @property
    def name(self):
        return self.NAME

    @property
    def output(self):
        """
        Return the contents of the "#output" div on the page.
        The fixtures are configured to update this div when the user
        interacts with the page.
        """
        text_list = self.css_text('#output')

        if len(text_list) < 1:
            return None
        else:
            return text_list[0]


class ButtonPage(SitePage):
    """
    Page for testing button interactions.
    """
    NAME = "button"

    def click_button(self):
        """
        Click the button on the page, which should cause the JavaScript
        to update the #output div.
        """
        self.css_click('div#fixture input')


class TextFieldPage(SitePage):
    """
    Page for testing text field interactions.
    """
    NAME = "text_field"

    def enter_text(self, text):
        """
        Input `text` into the text field on the page.
        """
        self.css_fill('#fixture input', text)


class SelectPage(SitePage):
    """
    Page for testing select input interactions.
    """
    NAME = "select"

    def select_car(self, car_value):
        """
        Select the car with `value` in the drop-down list.
        """
        self.select_option('cars', car_value)


class CheckboxPage(SitePage):
    """
    Page for testing checkbox interactions.
    """
    NAME = "checkbox"

    def toggle_pill(self, pill_name):
        """
        Toggle the box for the pill with `pill_name` (red or blue).
        """
        self.css_check('#fixture input#{0}'.format(pill_name))


class AlertPage(SitePage):
    """
    Page for testing alert handling.
    """
    NAME = "alert"

    def confirm(self):
        with self.handle_alert(confirm=True):
            self.css_click('button#confirm')

    def cancel(self):
        with self.handle_alert(confirm=False):
            self.css_click('button#confirm')

    def dismiss(self):
        with self.handle_alert():
            self.css_click('button#alert')


class SelectorPage(SitePage):
    """
    Page for testing retrieval of information by CSS selectors.
    """

    NAME = "selector"

    @property
    def num_divs(self):
        """
        Count the number of div.test elements.
        """
        return self.css_count('div.test')

    @property
    def div_text_list(self):
        """
        Return list of text for each div.test element.
        """
        return self.css_text('div.test')

    @property
    def div_value_list(self):
        """
        Return list of values for each div.test element.
        """
        return self.css_value('div.test')

    @property
    def div_html_list(self):
        """
        Return list of html for each div.test element.
        """
        return self.css_html('div.test')


class DelayPage(SitePage):
    """
    Page for testing elements that appear after a delay.
    """
    NAME = "delay"

    def trigger_output(self):
        """
        Wait for click handlers to be installed,
        then click a button and retrieve the output that appears
        after a delay.
        """

        click_ready = EmptyPromise(
            lambda: self.is_css_present('div#ready'), "Click ready"
        )

        output_ready = EmptyPromise(
            lambda: self.is_css_present('div#output'), "Output available"
        )

        with fulfill_after(output_ready):
            with fulfill_before(click_ready):
                self.css_click('div#fixture button')

    def make_broken_promise(self):
        """
        Make a promise that will not be fulfilled.
        Should raise a `BrokenPromise` exception.
        """
        bad_promise = EmptyPromise(
            lambda: self.is_css_present('div#not_present'), "Invalid div appeared",
            try_limit=3, try_interval=0.01
        )

        return fulfill(bad_promise)


class NextPage(SitePage):
    """
    Page that loads another page after a delay.
    """
    NAME = "next_page"

    def load_next(self, page_name, delay_sec):
        """
        Load the page named `page_name` after waiting for `delay_sec`.
        """
        time.sleep(delay_sec)
        self.ui.visit(page_name)


@js_defined('test_var1', 'test_var2')
class JavaScriptPage(SitePage):
    """
    Page for testing asynchronous JavaScript.
    """

    NAME = "javascript"

    @wait_for_js
    def trigger_output(self):
        """
        Click a button which will only work once RequireJS finishes loading.
        """
        self.css_click('div#fixture button')

    @wait_for_js
    def reload_and_trigger_output(self):
        """
        Reload the page, wait for JS, then trigger the output.
        """
        self.browser.reload()
        self.wait_for_js()
        self.css_click('div#fixture button')


@requirejs('main')
class RequireJSPage(SitePage):
    """
    Page for testing asynchronous JavaScript loaded with RequireJS.
    """

    NAME = "requirejs"

    @property
    @wait_for_js
    def output(self):
        return super(RequireJSPage, self).output
