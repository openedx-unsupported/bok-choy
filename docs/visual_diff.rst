Visual Diff Testing
===================

The bok-choy framework uses `Needle`_ to provide the ability to capture
portions of a rendered page in the browser and assert that the image captured
matches that of a baseline.  Needle is an optional dependency of bok-choy,
which you can install via either of the following commands:

.. code-block:: console

    pip install bok-choy[visual_diff]
    pip install needle

The general methodology for creating a test with a screenshot assertion
consists of the following steps.

* `Write Your Page Object and Test Case Code to Navigate the System Under Test`_
* `Add The Call to assertScreenshot`_
* `Create the Initial Baseline Screenshot`_
* `Execute Your Test Cases After Changes to the System Under Test`_
* `Advanced Features`_

Write Your Page Object and Test Case Code to Navigate the System Under Test
---------------------------------------------------------------------------

If you are not familiar with how to write a bok-choy page object and test case,
first check out the Tutorial. 

Here is an example of a test that navigates to the edx.org home page.

**page.py**, which contains the page object.

.. code-block:: python

    from bok_choy.page_object import PageObject

    class EdxHomePage(PageObject):
        url = 'http://www.edx.org'

        def is_browser_on_page(self):
            return 'edx' in self.browser.title.lower()

**my_test.py**, which contains the test code.

.. code-block:: python

    from bok_choy.web_app_test import WebAppTest
    from page import EdxHomePage

    class TestEdxHomePage(WebAppTest):

        def test_page_existence(self):
            EdxHomePage(self.browser).visit()

Add the Call to assertScreenshot
--------------------------------

``assertScreenshot()`` takes two arguments: a CSS selector for the element to
capture, and a filename for the image.

The following example uses the same **my_test.py** test case shown in the
previous section, with an assertion added to check that the site logo for the
edx.org home page has not changed.

* The first argument, ``img.site-logo`` is the css locator for the element
  that we want to capture and compare.

* The second argument, ``edx_logo_header`` is the filename that will be used
  for both the baseline and the actual results. The .png extension is appended
  automatically.

.. note:: For test reliability and synchronization purposes, a bok-choy best
   practice is to employ Promises to ensure that the page has been fully
   rendered before you take the screenshot. At the very least, you should
   first assert that the element you want to capture is present and visible on
   the screen.

**my_test.py**, with the screenshot assertion.

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


Create the Initial Baseline Screenshot
--------------------------------------

To create an initial screenshot of the logo, run the test case in "baseline
saving" mode by specifying the nose parameter ``--with-save-baseline``.

.. code-block:: bash

    $ nosetests my_test.py --with-save-baseline

If using pytest, you can instead set the environment variable
``NEEDLE_SAVE_BASELINE``.

.. code-block:: bash

    $ NEEDLE_SAVE_BASELINE=true py.test my_test.py

The folder in which the baseline and actual (output) screenshots are saved is
determined using the following environment variables.

* NEEDLE_OUTPUT_DIR - defaults to "screenshots"
* NEEDLE_BASELINE_DIR - defaults to "screenshots/baseline"

In our example, we would execute the test once with the save baseline
parameter to create screenshots/baseline/edx_logo_header.png. We would then
open it up and check that it looks okay.


Execute Your Test Cases After Changes to the System Under Test
--------------------------------------------------------------

Now if we run our tests, it will take the same screenshot and check it against
the saved baseline screenshot on disk.

.. code-block:: bash

    $ nosetests my_test.py

If a regression causes them to become significantly different, then the test
will fail.


Advanced Features
-----------------

See the `Needle documentation`_ for more information on the following advanced
features.

* Setting the viewport’s size - This feature is particularly useful for
  predicting the size of the resulting screenshots when taking full screen
  captures, and for testing responsive sites.

* Difference engine - Instead of PIL (the default), you might want to use
  PerceptualDiff. In addition to being much faster than PIL, PerceptualDiff
  generates a diff PNG file when a test fails, highlighting the differences
  between the baseline image and the new screenshot.

* File cleanup - Each time you run tests, new screenshot images are saved to
  disk, for comparison with the baseline screenshots. You might want to set
  your configuration to delete these files for all successful tests.


.. _Needle: https://github.com/bfirsh/needle
.. _Needle documentation: http://needle.readthedocs.org/
