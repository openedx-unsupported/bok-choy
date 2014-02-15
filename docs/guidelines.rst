Test-Design Guidelines
======================

To ensure that your tests are robust and maintainable, you should follow these guidelines:

1. Put browser interactions in the page object, not the test.
2. Put assertions in the test, not the page object.
3. Never use ``time.sleep()``
4. Always make pages wait for actions to complete.
5. Wait for JavaScript to load.


Put browser interactions in the page object, not the test
---------------------------------------------------------

When writing tests, it is sometimes tempting to query the browser directly.  For example, you might write a test like this:

.. code-block:: python

    class BarTest(WebAppTest):
        def test_bar(self):
            bar_text = self.browser.find_by_css('div.bar').text
            self.assertEqual(bar_text, "Bar")

Don't do this!  There are a number of problems with this approach:

1. If the CSS selector on the page changes, you will need to change every test that uses the CSS selector.

2. Selenium calls are notoriously unreliable.  They provide no retry logic to protect you from timing issues, which can cause intermittent test failures.  In contrast, ``bok-choy``'s higher-level interface for browser interactions include robust error-checking and retry logic.

Instead, encapsulate the browser interaction within a page object:

.. code-block:: python

    class BarPage(PageObject):
        def is_browser_on_page(self):
            return self.is_css_present('section#bar')

        @property
        def text(self):
            text_items = self.css_text('div.bar')
            if len(text_items) > 0:
                return text_items[0]
            else:
                return ""

Then use the page object in a test:

.. code-block:: python

    class BarTest(WebAppTest):
        def test_bar(self):
            bar_page = BarPage(self.browser)
            self.assertEqual(bar_page.text, "Bar")

The page object will first check that the browser is on the correct page before trying to use the page.  It will also retry if, for example, JavaScript modifies the ``<div>`` in between the time we retrieve it and when we get the element's text (this would result in a run-time exception otherwise).  Finally, if the CSS selector on the page changes, we can modify the page object, thus updating every test that interacts with the page.


Put assertions in the test, not the page object
-----------------------------------------------

Page objects allow tests to interact with the pages on a site.  But page objects should **not** make assertions about the page; that's the responsibility of the test.

For example, don't do this:

.. code-block:: python

    class BarPage(PageObject):
        def check_section_title(self):
            assert self.css_text('div.bar') == ['Test Section']

Because the page object contains the assertion, the page object is less re-usable.  If another test expects the page title to be something other than "Test Section", it cannot re-use ``check_section_title()``.

Instead, do this:

.. code-block:: python

    class BarPage(PageObject):
        def section_title(self):
            text_items = self.css_text('div.bar')
            if len(text_items) > 0:
                return text_items[0]
            else:
                return ""

Each test can then access the section title and assert that it matches what the test expects.


Never use ``time.sleep()``
--------------------------

Sometimes, tests fail because when they check the page too soon.  Often, tests must wait for JavaScript on the page to finish manipulating the DOM.  In these cases, it is tempting to insert an explicit wait using ``time.sleep()``.  For example:

.. code-block:: python

    class FooPage(PageObject):
        def do_foo(self):
            time.sleep(10)
            self.css_click('button.foo')

There are two problems with this approach:

1. Tests run more slowly, because they will always wait, even if the page is ready.
2. No matter how long the test waits, at some point it will not wait long enough.  This leads to intermittent test failures.

``bok-choy`` provides two mechanisms for dealing with timing issues.  First, each page object checks that the page is ready before interacting with the page:

.. code-block:: python

    class FooPage(PageObject):
        def is_browser_on_page(self):
            return self.is_css_present('button.foo')

        def do_foo(self):
            self.css_click('button.foo')

When you call ``do_foo()``, the page will wait for ``button.foo`` to be present in the DOM.

Second, the page object can use a ``Promise`` to wait for the DOM to be in a certain state.  For example, suppose that the page is ready when a "loading" message is no longer visible.  You could check this condition using a ``Promise``:

.. code-block:: python

    class FooPage(PageObject):
        def is_browser_on_page(self):
            return self.is_css_present('button.foo')

        def do_foo(self):
            ready_promise = EmptyPromise(
                lambda: 'Loading...' not in self.css_text('div.msg'),
                "Page finished loading"
            )

            with fulfill_before(ready_promise):
                self.css_click('button.foo')


Always make pages wait for actions to complete
----------------------------------------------

Page objects generally provide two ways of interacting with a page:
1. Querying the page for information.
2. Performing an action on the page.

In the second case, page objects should wait for the action to complete before returning.  For example, suppose a page object has a method ``save_document()`` that clicks a ``Save`` button.  The page then redirects to a different page.  In this case, the page object should wait for the next page to load before returning control to the caller.

.. code-block:: python

    class FooPage(PageObject):
        def save_document():
            self.css_click('button.save')
            return BarPage(self.browser).wait_for_page()

Tests can then use this page without worrying about whether the next page has loaded:

.. code-block:: python

    def test_save(self):
        bar = FooPage(self.browser).save_document()
        self.assertEqual(bar.text, "Bar")


Wait for JavaScript to load
---------------------------

Sometimes, a page is not ready until JavaScript on the page has finished loading.  This is especially problematic for pages that load JavaScript asynchronously (for example, when using `RequireJS <http://requirejs.org/>`_.

``bok-choy`` provides a simple mechanism for waiting for RequireJS modules to load:

.. code-block:: python

    @requirejs('foo')
    class FooPage(PageObject):

        @wait_for_js
        def text(self):
            return self.css_text('div.foo')

This will ensure that the RequireJS module ``foo`` has loaded before executing ``text()``.

More generally, you can wait for JavaScript variables to be defined:

.. code-block:: python

    @js_defined('window.Foo')
    class FooPage(PageObject):

        @wait_for_js
        def text(self):
            return self.css_text('div.foo')
