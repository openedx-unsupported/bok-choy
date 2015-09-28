Performing Accessibility Audits
==================================

The bok-choy framework includes the ability to perform accessibility audits on
web pages using either `Google Accessibility Developer Tools`_ or `Dequelabs Axe Core Accessibility Engine`_.

In each page object's definition you can define the audit rules to use for
checking that page and optionally, the scope of the audit within the webpage
itself.

The general methodology for enabling accessibility auditing consists of the
following steps.

* `Define the Accessibility Rules to Check for a Page`_
* `(Optional) Define the Scope of Accessibility Auditing for a Page`_
* Perform the audits either actively or passively.

  * Actively: `Trigger an Audit Actively and Assert on the Results Returned`_
  * Passively: `Leverage Your Existing Tests and Fail on Accessibility Errors`_

.. note:: Accessibility auditing is only supported with PhantomJS as the browser.


Define the Accessibility Rules to Check for a Page
--------------------------------------------------

A page object's list of audit rules to use in the accessibility audit for a
page are defined in the ``rules`` attribute of an A11yAuditConfig object.
This can be updated after instantiating the page object to be tested via the
``set_rules`` method.

The default is to check all the rules. To set this explicitly, pass an empty
list to ``set_rules``.

.. code-block:: python

    page.a11y_audit.config.set_rules([])

To skip automatic accessibility checking for a particular page, update the
page object's ``page.verify_accessibility`` attribute to return ``False``.

To check only a specific set of rules on a particular page, pass the list of
the names of the rules to that page's ``A11yAudit`` object's ``set_rules``
method.

.. code-block:: python

    page.a11y_audit.config.set_rules(
        ['badAriaAttributeValue', 'imagesWithoutAltText']
    )

To skip checking a specific set of rules on a particular page, pass the list
of the names of the rules as the first argument and ``ignore=True`` as the
second argument to that page's ``A11yAudit`` object's ``set_rules`` method.

.. code-block:: python

    page.a11y_audit.config.set_rules(
        ['badAriaAttributeValue', 'imagesWithoutAltText'],
        ignore=True
    )


(Optional) Define the Scope of Accessibility Auditing for a Page
----------------------------------------------------------------

You can limit the scope of an accessibility audit to only a portion of a page.
The default scope is the entire document.

To limit the scope, configure the page object's ``A11yAuditConfig`` object via
the ``set_scope`` method.

For instance, to start the accessibility audit in the ``div`` with id ``foo``,
you can follow this example.

.. code-block:: python

    page.a11y_audit.config.set_scope(["div#foo"])

Please see the rulset specific documentation for the ``set_scope`` method for
more details.


Trigger an Audit Actively and Assert on the Results Returned
--------------------------------------------------------------

To trigger an accessibility audit actively, call the page object class's
``a11y_audit.do_audit`` method and then assert on the results returned.

Here is an example of how you might write a test case that actively performs
an accessibility audit.

.. code-block:: python

    from bok_choy.page_object import PageObject


    class MyPage(PageObject):
        def __init__(self, *args, **kwargs):
            super(MyPage, self).__init__(*args, **kwargs)

            self.a11y_audit.config.set_rules(
                ['badAriaAttributeValue', 'imagesWithoutAltText']
            )

        def url(self):
            return 'https://www.mysite.com/page'


    class AccessibilityTest(WebAppTest):

        def test_accessibility_on_page(self):
            page = MyPage(self.browser)
            page.visit()
            report = page.a11y_audit.do_audit()

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
Here is an example of a bok-choy test that will implicity check for two
specific accessibility rules.


.. code-block:: python

    from bok_choy.page_object import PageObject


    class MyPage(PageObject):
        def __init__(self, *args, **kwargs):
            super(MyPage, self).__init__(*args, **kwargs)

            self.a11y_audit.config.set_rules(
                ['badAriaAttributeValue', 'imagesWithoutAltText']
            )

        def url(self):
            return 'https://www.mysite.com/page'

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
.. _Dequelabs Axe Core Accessibility Engine: https://github.com/dequelabs/axe-core
.. _audits folder: https://github.com/GoogleChrome/accessibility-developer-tools/tree/master/src/audits
.. _Selectors API: http://www.w3.org/TR/selectors-api/
