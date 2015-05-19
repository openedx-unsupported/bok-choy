Accessibility Testing
======================

The bok-choy framework includes the ability to test web pages for accessibility
using `Google Accessibility Developer Tools`_.

The audit rules that are checked and optionally the scope of the audit
within the webpage itself are defined on each Page Object's definition.

The general methodology for enabling accessibility auditing is:

* `Define the accessibility rules to check for a page`_
* `(optional) Define the scope for accessibility auditing of a page`_
* Perform the audits either:

  * Actively: `Trigger the audit actively and assert on the results returned`_
  * Passively: `Leverage your existing tests and fail on accessibility errors`_

.. note:: Accessibility auditing is only supported with PhantomJS as the browser.

Define the accessibility rules to check for a page
--------------------------------------------------

A page object's list of accessibility rules to audit for that page are defined
in the axs_audit_rules_to_run method.

The JavaScript code for the available rules can be found in the `audits folder`_
of the Google Accessibility Developer Tools repository. You can find the exact
spelling of each rule from the "name" attribute in its definition.

The default for page objects is to check all the rules. This is specified by
returning an empty list from the page object's axs_audit_rules_to_run method.

.. code-block:: python

    def axs_audit_rules_to_run(self):
        return []

To check only a single rule, or multiple rules, on a particular page,
configure the page object's axs_audit_rules_to_run method to return a list
with the name(s) of the rule(s).

.. code-block:: python

    def axs_audit_rules_to_run(self):
        return ['badAriaAttributeValue', 'imagesWithoutAltText']

To skip rules checking for a particular page, configure the page object's
axs_audit_rules_to_run method to return None.

.. code-block:: python

    def axs_audit_rules_to_run(self):
        return None

(optional) Define the scope for accessibility auditing of a page
----------------------------------------------------------------

You can limit the scope of the audit to a portion of the page.

The default for page objects is the entire document.

To limit the scope, configure the page object's axs_scope method to return the
element to use as the starting point via the `Selectors API`_.

For example if you want to start in the div with id 'foo' then you would use
the following:

.. code-block:: python

    def axs_scope(self):
        return 'document.querySelector("div#foo")'


Trigger the audit actively and assert on the results returned
--------------------------------------------------------------
Do this by calling the Page Object class's do_axs_audit method and then
asserting on the results returned.

Here is an example of how you might write a testcase that actively performs
an accessibility audit:

.. code-block:: python

    from bok_choy.page_object import PageObject
    class MyPage(PageObject):

        def url(self):
            return 'https://www.mysite.com/page'

        def axs_audit_rules_to_run(self):
            return ['badAriaAttributeValue', 'imagesWithoutAltText']


    class AccessibilityTest(WebAppTest):

        def test_accessibility_on_page(self):
            page = MyPage(self.browser)
            page.visit()
            report = page.do_axs_audit()

            # There was one page in this session
            self.assertEqual(1, len(report))
            result = report[0]

            # I have already corrected any accessibility errors on my page
            # for the rules I defined in the page object, so I will assert
            # that none exist.
            self.assertEqual(0, len(result.errors))
            self.assertEqual(0, len(result.warnings))


Leverage your existing tests and fail on accessibility errors
-------------------------------------------------------------
Do this by setting the VERIFY_ACCESSIBILITY environment variable to True.
This will trigger an accessibility audit whenever a Page Object's wait_for_page
method is called, and raise an AccessibilityError if errors are found on the page.

You might already have some bok-choy tests written for your web application.
Here is an example of one:


.. code-block:: python

    from bok_choy.page_object import PageObject
    class MyPage(PageObject):

        def url(self):
            return 'https://www.mysite.com/page'

        def axs_audit_rules_to_run(self):
            return ['badAriaAttributeValue', 'imagesWithoutAltText']

        def click_button(self):
            """
            Click on the button element (id="button").
            On my example page this will trigger an ajax call
            that updates the #output div with the text "yes!"
            """
            self.q(css='div#fixture button').first.click()
            self.wait_for_ajax()

        @property
        def output(self):
            """
            Return the contents of the "#output" div on the page.
            """
            text_list = self.q(css='#output').text

            if len(text_list) < 1:
                return None
            else:
                return text_list[0]

    class MyPageTest(WebAppTest):

        def test_button_click_output(self):
            page = MyPage(self.browser)
            page.visit()
            page.click_button()

            self.assertEqual(page.output, 'yes!')


You can reuse your existing bok-choy tests in order to navigate through
the application while at the same time verifying that it is accessibile.

Before running your bok-choy tests, set the environment variable
VERIFY_ACCESSIBILITY to true.

::

    export VERIFY_ACCESSIBILITY=True

This will trigger an audit, using the rules (and optionally the scope) set in
the page object definition, whenever a call to wait_for_page() is made.

In the case of the test_button_click_output testcase in the above example,
an audit will be done at the end of the visit() and click_button() method calls,
as each of those will call out to wait_for_page().

If any assessibility errors are found, then the testcase will fail with an
AccessibilityError.

.. note:: An AccessibilityError is raised only on errors, not on warnings.

.. _Google Accessibility Developer Tools: https://github.com/GoogleChrome/accessibility-developer-tools
.. _audits folder: https://github.com/GoogleChrome/accessibility-developer-tools/tree/master/src/audits
.. _Selectors API: http://www.w3.org/TR/selectors-api/
