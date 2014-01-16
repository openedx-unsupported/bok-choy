############
Introduction
############

`Bok Choy`_ is a UI-level acceptance test framework for writing robust Selenium_ tests in Python_.

`Bok Choy`_ makes your acceptance tests reliable and maintainable by utilizing the
`Page Object <https://code.google.com/p/selenium/wiki/PageObjects>`_ and
`Promise <http://www.quora.com/JavaScript/What-is-the-promise-pattern>`_
design patterns.

The general pattern is to:
Define Page => Write Tests for Page => Execute Tests => Repeat, adding more pages and tests


*****
Setup
*****

As Bok Choy is a Python_ framework, you first need to install Python.
If you’re running Linux or Mac OS X, you probably already have it installed.
We recommend that you use `pip <http://www.pip-installer.org/>`_ to install your python
packages. To install Bok Choy into your Python installation’s site-packages directory:

.. code-block:: bash

   sudo pip install bok-choy


********************
Let's start testing!
********************

For this tutorial, we will visit the GitHub site and execute a search for EdX's version of
its OpenSource MOOC platform, and verify the results returned.


Folder structure
================

Your test will be a Python module, so let's get started by defining it as such. Make a folder for
your project, and inside that create an empty file named ``__init__.py``.

.. code-block:: bash

    /home/user/bok-choy-tutorial
        - __init__.py


.. code-block:: bash

   mkdir ~/bok-choy-tutorial
   cd ~/bok-choy-tutorial
   touch __init__.py


Round 1 - The framework of a test
=================================

Let's set up and execute a simple test to make sure that all the pieces are installed
and working properly.


Define the page
---------------

The first step is to define the page object for the page of the web application that you will
be interacting with. This includes the name of the page and a method to check whether the browser
is on the page. If it is possible to navigate directly to the page, we want to tell the page object
how to do that too.

Create a file named pages.py in your project folder and define the GitHubSearchPage page object
as follows:

.. code-block:: bash

    /home/user/bok-choy-tutorial
        - __init__.py
        - pages.py


.. code-block:: python

    # -*- coding: utf-8 -*-
    from bok_choy.page_object import PageObject

    class GitHubSearchPage(PageObject):
        """
        GitHub's search page
        """

        @property
        def url(self):
            return 'http://www.github.com/search'

        def is_browser_on_page(self):
            return 'code search' in self.browser.title.lower()


Write a test for the page
-------------------------

Write the first test, which will open up a browser, navigate to the page we just defined,
and verify that we got there.

Create a file named test_search.py in your project folder and use it to visit the page as follows:

.. code-block:: bash

    /home/user/bok-choy-tutorial
        - __init__.py
        - pages.py
        - test_search.py


.. code-block:: python

    import unittest
    from bok_choy.web_app_test import WebAppTest
    from pages import GitHubSearchPage

    class TestGitHub(WebAppTest):
        """
        Tests for the GitHub site.
        """

        def test_page_existence(self):
            """
            Make sure that the page is accessible.
            """
            GitHubSearchPage(self.ui).visit()


    if __name__ == '__main__':
        unittest.main()


Execute the test
----------------

Execute the test from the command line with the following.

.. code-block:: bash

   python test_search.py


.. code-block:: bash

    .
    ----------------------------------------------------------------------
    Ran 1 test in 3.417s

    OK


What just happened?
-------------------

You should have seen your default browser launch and navigate to the GitHub search
page. It knew how to get there because of the page object's 'url' property.

Once the browser navigated to the page, it knew it was on the right page because the page's
'is_browser_on_page' method returned True.


Round 2 - Interacting with a page
=================================

Let's circle back around to improve the definition of the page and have the test do
something more interesting, like searching for something.


Improve the page definition
---------------------------

.. tip:: A Best Practice for Bok Choy tests is to use css locators to identify objects.

.. hint:: Get to know how to use the developer tools for your favorite browser.
    Here are links to articles to get you started with Chrome_ and Firefox_.

.. _Chrome: https://developers.google.com/chrome-developer-tools/docs/dom-and-styles
.. _FireFox: https://developer.mozilla.org/en-US/docs/Tools/Page_Inspector


Edit your page.py file to add in the input field where you type in text and the search button.
Using the Developer Tools for my browser, I see that the input field can be identified
by its type (input) and id (js-command-bar-field), so its css locator would be "input#js-command-bar-field".

.. code-block:: xml

    <input type="text" data-hotkey="/ s" name="q" id="js-command-bar-field" placeholder="Search or type a command">


Add a method for filling in the search term to the page object definition like this:

.. code-block:: python
   :emphasize-lines: 19-23

    # -*- coding: utf-8 -*-
    from bok_choy.page_object import PageObject

    class GitHubSearchPage(PageObject):
        """
        GitHub's search page
        """

        @property
        def url(self):
            return 'http://www.github.com/search'

        def is_browser_on_page(self):
            return 'code search' in self.browser.title.lower()

        def enter_search_terms(self, text):
            """
            Fill the text into the input field
            """
            self.css_fill('input#js-command-bar-field', text)


What's next? I see that type (button) and class (button) are good way to identify the search button.
Its css locator would be "button.button".

.. code-block:: xml

    <button class="button" type="submit" tabindex="3">Search</button>


We will need to define how to press the button. But we also want to define how we know that
pressing the button really worked. Try it yourself in a browser. While I'm writing this tutorial,
the way the GitHub search currently works is to bring you to a search results page (as long as you
entered text into the input field).

So before we add the method for clicking the Search button, we should add the definition for the
search results page to pages.py. If we want to use the page title again, we can see that when you
search for "foo bar" it will be:

.. code-block:: xml

    <title>Search · foo bar</title>


Add another page's definition
-----------------------------

So we add the search results page definition to pages.py:

.. code-block:: python

    # -*- coding: utf-8 -*-
    from bok_choy.page_object import PageObject
    import re

    [...]

    class GitHubSearchResultsPage(PageObject):
        """
        GitHub's search results page
        """

        def __init__(self, search_phrase):
            super(GitHubSearchResultsPage, self).__init__(ui)
            self.search_phrase = search_phrase

        @property
        def url(self):
            """
            You do not navigate here directly
            """
            raise NotImplemented

        def is_browser_on_page(self):
            # This should be something like: u'Search · foo bar'
            title = self.browser.title
            matches = re.match(u'^Search · {}'.format(self.search_phrase), title)
            return matches is not None


Define the search method
------------------------

Back to defining a method for pressing the button and knowing that you have arrived at the
results page: We want to press the button, then wait and make sure that you have arrived at
the results page before continuing on. Page objects in Bok Choy have a wait_for_page method
that does just that.

Let's see how the method definition for pressing the search button would look.

.. code-block:: python
   :emphasize-lines: 26-40

    # -*- coding: utf-8 -*-
    from bok_choy.page_object import PageObject
    import re

    class GitHubSearchPage(PageObject):
        """
        GitHub's search page
        """
        INPUT_SELECTOR = 'input#js-command-bar-field'

        @property
        def url(self):
            return 'http://www.github.com/search'

        def is_browser_on_page(self):
            return 'code search' in self.browser.title.lower()

        def enter_search_terms(self, text):
            """
            Fill the text into the input field
            """
            self.css_fill(self.INPUT_SELECTOR, text)

        def search(self):
            """
            Click on the Search button and wait for the
            results page to be displayed
            """
            self.css_click('button.button')
            results = GitHubSearchResultsPage(self.ui, self.INPUT_SELECTOR)
            results.wait_for_page()
            return results

        def search_for_terms(self, text):
            """
            Fill in the search terms and click the
            Search button
            """
            self.enter_search_terms(text)
            return self.search()


    class GitHubSearchResultsPage(PageObject):
        """
        GitHub's search results page
        """

        def __init__(self, search_phrase):
            super(GitHubSearchResultsPage, self).__init__(ui)
            self.search_phrase = search_phrase

        @property
        def url(self):
            """
            You do not navigate here directly
            """
            raise NotImplemented

        def is_browser_on_page(self):
            # This should be something like: u'Search · foo bar'
            title = self.browser.title
            matches = re.match(u'^Search · {}'.format(self.search_phrase), title)
            return matches is not None


Add the new test
----------------

Now let's add the new test to test_search.py:

.. code-block:: python
   :emphasize-lines: 20-25

    import unittest
    from bok_choy.web_app_test import WebAppTest
    from pages import GitHubSearchPage

    class TestGitHub(WebAppTest):
        """
        Tests for the GitHub site.
        """

        def setUp(self):
            super(TestGitHub, self).setUp()
            self.github_search = GitHubSearchPage(self.ui)

        def test_page_existence(self):
            """
            Make sure that the page is accessible.
            """
            self.github_search.visit()

        def test_search(self):
            """
            Make sure that you can search for something.
            """
            self.github_search.visit()
            self.github_search.search_for_terms('user:edx repo:edx-platform')


    if __name__ == '__main__':
        unittest.main()

Run it!
-------

.. code-block:: bash

   python test_search.py


.. code-block:: bash

    ..
    ----------------------------------------------------------------------
    Ran 2 tests in 8.478s

    OK


What just happened?
-------------------

The first test ran, just as before. Now the second test ran too: it entered the search term,
hit the search button, and verified that it got to the results page.


Round 3 - Search and verify results
===================================

In the test version that we just completed we entered some search terms and
then verified that we got to the right page, but not that the correct results
were returned. Let's improve our test to verify the search results.

Improve the page definition
---------------------------

Since we want to verify the results of the search, we need to add a property for the
results returned to the page object for the search results page.

.. code-block:: python
   :emphasize-lines: 64-70

    # -*- coding: utf-8 -*-
    from bok_choy.page_object import PageObject
    import re

    class GitHubSearchPage(PageObject):
        """
        GitHub's search page
        """
        INPUT_SELECTOR = 'input#js-command-bar-field'

        @property
        def url(self):
            return 'http://www.github.com/search'

        def is_browser_on_page(self):
            return 'code search' in self.browser.title.lower()

        def enter_search_terms(self, text):
            """
            Fill the text into the input field
            """
            self.css_fill(self.INPUT_SELECTOR, text)

        def search(self):
            """
            Click on the Search button and wait for the
            results page to be displayed
            """
            self.css_click('button.button')
            results = GitHubSearchResultsPage(self.ui, self.INPUT_SELECTOR)
            results.wait_for_page()
            return results

        def search_for_terms(self, text):
            """
            Fill in the search terms and click the
            Search button
            """
            self.enter_search_terms(text)
            return self.search()


    class GitHubSearchResultsPage(PageObject):
        """
        GitHub's search results page
        """

        def __init__(self, ui, search_phrase):
            super(GitHubSearchResultsPage, self).__init__(ui)
            self.search_phrase = search_phrase

        @property
        def url(self):
            """
            You do not navigate here directly
            """
            raise NotImplemented

        def is_browser_on_page(self):
            # This should be something like: u'Search · foo bar'
            title = self.browser.title
            matches = re.match(u'^Search · {}'.format(self.search_phrase), title)
            return matches is not None

        @property
        def search_results(self):
            """
            Return a list of results returned from a search
            """
            return self.css_text('ul.repolist > li > h3.repolist-name > a')


Improve the search test
-----------------------

Now we want to verify that edx-platform repo for the EdX account was returned in the
search results. And not only that, but also that it was the first result.
Modify the test.py file to do these assertions:

.. code-block:: python
   :emphasize-lines: 3, 12, 26-27

    import unittest
    from bok_choy.web_app_test import WebAppTest
    from pages import GitHubSearchPage, GitHubSearchResultsPage

    class TestGitHub(WebAppTest):
        """
        Tests for the GitHub site.
        """

        def setUp(self):
            super(TestGitHub, self).setUp()
            self.github_search = GitHubSearchPage(self.ui)

        def test_page_existence(self):
            """
            Make sure that the page is accessible.
            """
            self.github_search.visit()

        def test_search(self):
            """
            Make sure that you can search for something.
            """
            self.github_search.visit()
            search_results_page = self.github_search.search_for_terms('user:edx repo:edx-platform')
            search_results = search_results_page.search_results
            assert 'edx/edx-platform' in search_results
            assert search_results[0] == 'edx/edx-platform'


    if __name__ == '__main__':
        unittest.main()

Run it!
-------

.. code-block:: bash

   python test_search.py


.. code-block:: bash

    ..
    ----------------------------------------------------------------------
    Ran 2 tests in 7.692s

    OK


What just happened?
-------------------

Both tests ran. We verified that we could get to the GitHub search page, then
we searched for the EdX user's edx-platform repo and verified that it was the
first result returned.

******************
Take it from here!
******************

This tutorial should have gotten you going with defining page objects for a web application
and how to start to write tests against the app. Now it's up to you to take it from here and
start testing your own web application. Have fun!
