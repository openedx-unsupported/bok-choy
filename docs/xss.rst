Performing XSS Vulnerability Audits
===================================

The bok-choy framework includes the ability to perform XSS (cross-site scripting) audits on
web pages using a short XSS locator defined in
https://www.owasp.org/index.php/XSS_Filter_Evasion_Cheat_Sheet#XSS_Locator.

Trigger XSS Vulnerability Audits in Existing Tests
--------------------------------------------------

You might already have some bok-choy tests written for your web application. To
leverage existing bok-choy tests and have them fail on finding XSS vulnerabilities,
follow these steps.

1. Insert the ``XSS_INJECTION`` string defined in ``bok_choy.page_object`` into your page content.
2. Set the ``VERIFY_XSS`` environment variable to ``True``.

::

    export VERIFY_XSS=True


With this environment variable set, an XSS audit is triggered whenever a page object's ``q``
method is called. The audit will detect improper escaping both in HTML and in Javascript
that is embedded within HTML.

If errors are found on the page, an XSSExposureError is raised.

Here is an example of a bok-choy test that will check for XSS vulnerabilities.
It clicks a button on the page, and the user's name is inserted into the page.
If the user name is not properly escaped, the display
of the name (which is data provided by the user and thus potentially malicious) can cause
XSS issues.

In the case of the ``test_button_click_output`` test case in the example below,
an audit will be done in the ``click_button()``, ``output()``, and ``visit()`` method calls,
as each of those will call out to ``q``.

If any XSS errors are found, then the test case will fail with an
XSSExposureError.

.. code-block:: python

    from bok_choy.page_object import PageObject, XSS_INJECTION


    class MyPage(PageObject):
        def url(self):
            return 'https://www.mysite.com/page'

        def is_browser_on_page(self):
            return self.q(css='div#fixture button').present

        def click_button(self):
            """
            Click on the button element (id="button").
            On my example page this will trigger an ajax call
            that updates the #output div with the user's name.
            """
            self.q(css='div#fixture button').first.click()
            self.wait_for_ajax()

        @property
        def output(self):
            """
            Return the contents of the "#output" div on the page.

            In the example page, it will contain the user's name after being
            updated by the ajax call that is triggered by clicking the button.
            """
            text_list = self.q(css='#output').text

            if len(text_list) < 1:
                return None
            else:
                return text_list[0]

    class MyPageTest(WebAppTest):
        def setUp(self):
            """
            Log in as a particular user.
            """
            super(MyPageTest, self).setUp()
            self.user_name = XSS_INJECTION
            self.log_in_as_user(self.user_name)

        def test_button_click_output(self):
            page = MyPage(self.browser)
            page.visit()
            page.click_button()

            self.assertEqual(page.output, self.user_name)

        def log_in_as_user(self, user_name):
            """
            Would be implemented to log in as a particular user
            with a potentially malicious, user-provided name.
            """
            pass

