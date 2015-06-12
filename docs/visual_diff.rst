Visual Diff Testing
===================

The bok-choy framework uses `Needle`_ to provide the ability to capture portions of a rendered page
in the browser and assert that the image captured matches that of a baseline.

The general methodology for creating a test with a screenshot assertion is:

* `Write your page object and testcase code to navigate the system under test`_
* `Add the call to assertScreenshot`_
* `Create the initial baseline screenshot`_
* `Execute your testcases after changes to the system under test`_
* `Advanced features`_

Write your page object and testcase code to navigate the system under test
--------------------------------------------------------------------------
If you are not familiar with how to write a bok-choy page object and testcase, first check out the Tutorial.
Here is an example of a test that navigates to the edx.org home page.

**page.py**, which contains the page object:

.. code-block:: python

    from bok_choy.page_object import PageObject

    class EdxHomePage(PageObject):
        url = 'http://www.edx.org'

        def is_browser_on_page(self):
            return 'edx' in self.browser.title.lower()

**my_test.py**, which contains the test code:

.. code-block:: python

    from bok_choy.web_app_test import WebAppTest
    from page import EdxHomePage

    class TestEdxHomePage(WebAppTest):

        def test_page_existence(self):
            EdxHomePage(self.browser).visit()

Add the call to assertScreenshot
--------------------------------
assertScreenshot() take two arguments: a CSS selector for the element to capture and a filename for the image.
Here is the same testcase, with an assertion added that will ensure that the site logo for the edx.org home
page has not changed.

* The first argument, "img.site-logo" is the css locator for the element that we want to capture and compare.
* The second argument, "edx_logo_header" is the filename (.png will be appended automatically) that will be used
  for both the baseline and the actual results.

.. note:: For test reliability and synchronization purposes, a bok-choy best practice is to employ Promises to ensure
   that the page has been fully rendered before you take the screenshot. At the very least, you should first assert that
   the element you want to capture is present and visible on the screen.

**my_test.py**, with the screenshot assertion:

.. code-block:: python
    :emphasize-lines: 7-10

    from bok_choy.web_app_test import WebAppTest
    from page import EdxHomePage

    class TestEdxHomePage(WebAppTest):

        def test_page_existence(self):
            homepage = EdxHomePage(self.browser).visit()
            css_locator = 'img.site-logo'
            self.assertTrue(homepage.q(css=css_locator).first.visible)
            self.assertScreenshot(css_locator, 'edx_logo_header')

Create the initial baseline screenshot
--------------------------------------
To create an initial screenshot of the logo, run in ‘baseline saving’ mode
by specifying the nose parameter --with-save-baseline.

.. code-block:: bash

    $ nosetests my_test.py --with-save-baseline

The folder in which the baseline and actual (output) screenshots are saved is determined via the following
environment variables:

* NEEDLE_OUTPUT_DIR - defaults to "screenshots"
* NEEDLE_BASELINE_DIR - defaults to "screenshots/baseline"

In our example, we would execute the test once with the save baseline parameter to create
screenshots/baseline/edx_logo_header.png. We would then open it up and check that it looks okay.

Execute your testcases after changes to the system under test
-------------------------------------------------------------
Now if we run our tests, it will take the same screenshot and check it against the screenshot on disk:

.. code-block:: bash

    $ nosetests my_test.py

If a regression causes them to become significantly different, then the test will fail.

Advanced features
-----------------

See the `Needle documentation`_ for more information on these advanced features:

* Setting the viewport’s size - This is particularly useful for predicting the size of the resulting screenshots
  when taking fullscreen captures, and for testing responsive sites.
* Difference engine - Instead of PIL (the default), you may want to use PerceptualDiff. Besides being much faster
  than PIL, PerceptualDiff also generates a diff PNG file when a test fails, highlighting the differences between the
  baseline image and the new screenshot.
* File cleanup - Each time you run tests, new screenshot images are saved to disk, for comparison with the
  baseline screenshots. You may want to set your configuration to delete these files for all successful tests.


.. _Needle: https://github.com/bfirsh/needle
.. _Needle documentation: http://needle.readthedocs.org/
