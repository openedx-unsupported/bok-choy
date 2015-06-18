Performing Accessibility Audits
==================================

The bok-choy framework includes the ability to perform accessibility audits on
web pages using `Google Accessibility Developer Tools`_.

In each page object's definition you can define the audit rules to use for
checking that page and optionally, the scope of the audit within the webpage
itself.

The general methodology for enabling accessibility auditing consists of the
following steps.

* `Define the Audit Rules to Check for a Page`_
* `(Optional) Define the Scope of Accessibility Auditing for a Page`_
* Perform the audits either actively or passively.

  * Actively: `Trigger an Audit Actively and Assert on the Results Returned`_
  * Passively: `Leverage Your Existing Tests and Fail on Accessibility Errors`_

.. note:: Accessibility auditing is only supported with PhantomJS as the browser.


Define the Audit Rules to Check for a Page
--------------------------------------------

A page object's list of audit rules to use in the accessibility audit for a
page are defined in the ``axs_audit_rules_to_run`` method.

The JavaScript code for the available rules can be found in the `audits folder`_
of the Google Accessibility Developer Tools repository. You can find the exact
spelling of each rule from the "name" attribute in its definition.

The default for page objects is to check all the rules. This is specified by
returning an empty list from the page object's ``axs_audit_rules_to_run`` method.

.. code-block:: python

    def axs_audit_rules_to_run(self):
        return []

To check only a single rule, or multiple rules, on a particular page,
configure the page object's ``axs_audit_rules_to_run`` method to return a list
with the name(s) of the rule(s).

.. code-block:: python

    def axs_audit_rules_to_run(self):
        return ['badAriaAttributeValue', 'imagesWithoutAltText']

To skip rules checking for a particular page, configure the page object's
``axs_audit_rules_to_run`` method to return ``None``.

.. code-block:: python

    def axs_audit_rules_to_run(self):
        return None


To run all rules *except* for specific ones, configure the page object's
``axs_audit_rules_to_ignore`` method to return a list of the rules you do not
want to check. This list will take precedence over the list of rules in
``axs_audit_rules_to_run``. For instance, in the following example, the rule
``badAriaAttributeValue`` would be ignored even if it was also listed in the
page object's ``axs_audit_rules_to_run`` method.

.. code-block:: python

    def axs_audit_rules_to_ignore(self):
        return ['badAriaAttributeValue']

(*Default*) Defining ``axs_audit_rules_to_ignore`` to return an empty list
will result in the rules being run in the way that they are defined by
``axs_audit_rules_to_run``.

.. code-block:: python

    def axs_audit_rules_to_ignore(self):
        return []


(Optional) Define the Scope of Accessibility Auditing for a Page
----------------------------------------------------------------

You can limit the scope of an accessibility audit to only a portion of a page.

The default for page objects is the entire document.

To limit the scope, configure the page object's ``axs_scope`` method to return the
element that you want to use as the starting point via the `Selectors API`_.

For instance, to start the accessibility audit in the ``div`` with id ``foo``,
you can follow this example.

.. code-block:: python

    def axs_scope(self):
        return 'document.querySelector("div#foo")'


Trigger an Audit Actively and Assert on the Results Returned
--------------------------------------------------------------

To trigger an accessibility audit actively, call the page object class's
``do_axs_audit`` method and then assert on the results returned.

Here is an example of how you might write a test case that actively performs
an accessibility audit.

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


Leverage Your Existing Tests and Fail on Accessibility Errors
-------------------------------------------------------------

To trigger accessibility audits passively, set the ``VERIFY_ACCESSIBILITY``
environment variable to ``True``. Doing so triggers an accessibility audit
whenever a page object's ``wait_for_page`` method is called. If errors are
found on the page, an AccessibilityError is raised.

.. note:: An AccessibilityError is raised only on errors, not on warnings.

You might already have some bok-choy tests written for your web application.
Here is an example of a bok-choy test.


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
``VERIFY_ACCESSIBILITY`` to ``True``.

::

    export VERIFY_ACCESSIBILITY=True

This will trigger an audit, using the rules (and optionally the scope) set in
the page object definition, whenever a call to ``wait_for_page()`` is made.

In the case of the ``test_button_click_output`` test case in the example above,
an audit will be done at the end of the ``visit()`` and ``click_button()`` method calls,
as each of those will call out to ``wait_for_page()``.

If any assessibility errors are found, then the testcase will fail with an
AccessibilityError.

.. note:: An AccessibilityError is raised only on errors, not on warnings.


.. _Google Accessibility Developer Tools: https://github.com/GoogleChrome/accessibility-developer-tools
.. _audits folder: https://github.com/GoogleChrome/accessibility-developer-tools/tree/master/src/audits
.. _Selectors API: http://www.w3.org/TR/selectors-api/
