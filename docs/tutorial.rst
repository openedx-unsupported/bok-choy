********************
Tutorial
********************

For this tutorial, we will visit GitHub, execute a search for EdX's version of
its open source MOOC platform, and verify the results returned.


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


.. literalinclude:: code/round_1/pages.py
    :language: python



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


.. literalinclude:: code/round_1/test_search.py
    :language: python



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
Using the Developer Tools for my browser, I see that the input field can be identified by combining form tags
id (#search_form) and input tags type (text), so its css locator would be '#search_form > input[type="text"]'.

.. code-block:: xml

    <form accept-charset="UTF-8" action="/search" class="search_repos" id="search_form" method="get">
        <input type="text" data-hotkey="s" name="q" placeholder="Search GitHub" tabindex="1" autocapitalize="off" autofocus="" autocomplete="off" spellcheck="false">


Add a method for filling in the search term to the page object definition like this:


.. literalinclude:: code/round_2/pages.py
    :language: python
    :lines: 31-35


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

.. literalinclude:: code/round_2/pages.py
    :language: python
    :lines: 6-18


Define the search method
------------------------

Back to defining a method for pressing the button and knowing that you have arrived at the
results page: We want to press the button, then wait and make sure that you have arrived at
the results page before continuing on. Page objects in Bok Choy have a ``wait_for_page`` method
that does just that.

Let's see how the method definition for pressing the search button would look.

.. literalinclude:: code/round_2/pages.py
    :language: python
    :lines: 21-51



Add the new test
----------------

Now let's add the new test to test_search.py:

.. literalinclude:: code/round_2/test_search.py
    :language: python


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

Improve the page definitions
----------------------------
Since we want to verify the results of the search, we need to add a property for the
results returned to the page object for the search results page.

.. literalinclude:: code/round_3/pages.py
    :language: python
    :lines: 1-24

Also maybe we want a better way to determine that we are on the search page than 
just the words "code search" the title. Let's use a query to make sure that the 
search button exists.

.. literalinclude:: code/round_3/pages.py
    :language: python
    :lines: 27-35


Improve the search test
-----------------------

Now we want to verify that edx-platform repo for the EdX account was returned in the
search results. And not only that, but also that it was the first result.
Modify the test.py file to do these assertions:

.. literalinclude:: code/round_3/test_search.py
    :language: python


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


Take it from here!
==================

This tutorial should have gotten you going with defining page objects for a web application
and how to start to write tests against the app. Now it's up to you to take it from here and
start testing your own web application. Have fun!
