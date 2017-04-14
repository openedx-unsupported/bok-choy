"""
Tools for interacting with the DOM inside a browser.
"""
from __future__ import absolute_import

import logging

from copy import copy
from collections import Sequence
from itertools import islice
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
import six
from bok_choy.promise import Promise


LOGGER = logging.getLogger(__name__)

# Mapping of query type to Selenium webdriver query method names
QUERY_TYPES = {
    'css': By.CSS_SELECTOR,
    'xpath': By.XPATH,
    'class': By.CLASS_NAME,
    'id': By.ID,
    'link': By.LINK_TEXT,
    'name': By.NAME,
    'partial_link': By.PARTIAL_LINK_TEXT,
    'tag': By.TAG_NAME,
}


def no_error(func):
    """
    Decorator to create a `Promise` check function that is satisfied
    only when `func` executes without a Selenium error.

    This protects against many common test failures due to timing issues.
    For example, accessing an element after it has been modified by JavaScript
    ordinarily results in a `StaleElementException`.  Methods decorated
    with `no_error` will simply retry if that happens, which makes tests
    more robust.

    Args:
        func (callable): The function to execute, with retries if an error occurs.

    Returns:
        Decorated function
    """
    def _inner(*args, **kwargs):  # pylint: disable=missing-docstring
        try:
            return_val = func(*args, **kwargs)
        except WebDriverException:
            LOGGER.warning(u'Exception ignored during retry loop:', exc_info=True)
            return False, None
        else:
            return True, return_val

    return _inner


class Query(Sequence):
    """
    General mechanism for selecting and transforming values.
    """

    def __init__(self, seed_fn, desc=None):
        """
        Configure the `Query`.

        Args:
            seed_fn (callable): Callable with no arguments that produces a list of values.

        Keyword Args:
            desc (str): A description of the query, used in log messages.
                If not provided, defaults to the name of the seed function.

        Returns:
            Query
        """
        if desc is None:
            desc = u'Query({})'.format(getattr(seed_fn, '__name__', ''))

        self.seed_fn = seed_fn
        self.transforms = []
        self.desc_stack = []
        self.desc = desc

    def replace(self, **kwargs):
        """
        Return a copy of this `Query`, but with attributes specified
        as keyword arguments replaced by the keyword values.

        Keyword Args:
            Attributes/values to replace in the copy.

        Returns:
             A copy of the query that has its attributes updated with the specified values.

        Raises:
            TypeError: The `Query` does not have the specified attribute.
        """
        clone = copy(self)

        clone.transforms = list(clone.transforms)
        for key, value in kwargs.items():
            if not hasattr(clone, key):
                raise TypeError('replace() got an unexpected keyword argument {!r}'.format(key))

            setattr(clone, key, value)
        return clone

    def transform(self, transform, desc=None):
        """
        Create a copy of this query, transformed by `transform`.

        Args:
            transform (callable): Callable that takes an iterable of values and
                returns an iterable of transformed values.

        Keyword Args:
            desc (str): A description of the transform, to use in log messages.
                Defaults to the name of the `transform` function.

        Returns:
            Query
        """
        if desc is None:
            desc = u'transform({})'.format(getattr(transform, '__name__', ''))

        return self.replace(
            transforms=self.transforms + [transform],
            desc_stack=self.desc_stack + [desc]
        )

    def map(self, map_fn, desc=None):
        """
        Return a copy of this query, with the values mapped through `map_fn`.

        Args:
            map_fn (callable): A callable that takes a single argument and returns a new value.

        Keyword Args:
            desc (str): A description of the mapping transform, for use in log message.
                Defaults to the name of the map function.

        Returns:
            Query
        """
        if desc is None:
            desc = getattr(map_fn, '__name__', '')
        desc = u'map({})'.format(desc)

        return self.transform(lambda xs: (map_fn(x) for x in xs), desc=desc)

    def flat_map(self, map_fn, desc=None):
        """
        Return a copy of this query, with the values mapped through `map_fn`, and then the resulting list flattened.

        Args:
            map_fn (callable): A callable that takes a single argument and returns a new value.

        Keyword Args:
            desc (str): A description of the mapping transform, for use in log message.
                Defaults to the name of the map function.

        Returns:
            Query
        """
        if desc is None:
            desc = getattr(map_fn, '__name__', '')
        desc = u'flat_map({})'.format(desc)

        return self.transform(lambda xs: sum((map_fn(x) for x in xs), []), desc=desc)

    def filter(self, filter_fn=None, desc=None, **kwargs):
        """
        Return a copy of this query, with some values removed.

        Example usages:

        .. code:: python

            # Returns a query that matches even numbers
            q.filter(filter_fn=lambda x: x % 2)

            # Returns a query that matches elements with el.description == "foo"
            q.filter(description="foo")

        Keyword Args:
            filter_fn (callable): If specified, a function that accepts one argument (the element)
                    and returns a boolean indicating whether to include that element in the results.

            kwargs: Specify attribute values that an element must have to be included in the results.

            desc (str): A description of the filter, for use in log messages.
                Defaults to the name of the filter function or attribute.

        Raises:
            TypeError: neither or both of `filter_fn` and `kwargs` are provided.
        """
        if filter_fn is not None and kwargs:
            raise TypeError('Must supply either a filter_fn or attribute filter parameters to filter(), but not both.')
        if filter_fn is None and not kwargs:
            raise TypeError('Must supply one of filter_fn or one or more attribute filter parameters to filter().')

        if desc is None:
            if filter_fn is not None:
                desc = getattr(filter_fn, '__name__', '')
            elif kwargs:
                desc = u", ".join([u"{}={!r}".format(key, value) for key, value in kwargs.items()])
        desc = u"filter({})".format(desc)

        if kwargs:
            def filter_fn(elem):  # pylint: disable=function-redefined, missing-docstring
                return all(
                    getattr(elem, filter_key) == filter_value
                    for filter_key, filter_value
                    in kwargs.items()
                )

        return self.transform(lambda xs: (x for x in xs if filter_fn(x)), desc=desc)

    def _execute(self):
        """
        Run the query, generating data from the `seed_fn` and performing transforms on the results.
        """
        data = self.seed_fn()
        for transform in self.transforms:
            data = transform(data)
        return list(data)

    def execute(self, try_limit=5, try_interval=0.5, timeout=30):
        """
        Execute this query, retrying based on the supplied parameters.

        Keyword Args:
            try_limit (int): The number of times to retry the query.
            try_interval (float): The number of seconds to wait between each try (float).
            timeout (float): The maximum number of seconds to spend retrying (float).

        Returns:
            The transformed results of the query.

        Raises:
            BrokenPromise: The query did not execute without a Selenium error after one or more attempts.
        """
        return Promise(
            no_error(self._execute),
            u"Executing {!r}".format(self),
            try_limit=try_limit,
            try_interval=try_interval,
            timeout=timeout,
        ).fulfill()

    @property
    def results(self):
        """
        A list of the results of the query, which are cached.
        If you call `results` multiple times on the same query, you will always get the same results.
        Use `reset()` to clear the cache and re-run the query.

        Returns:
            The results from executing the query.
        """
        return self.execute()

    def __getitem__(self, key):
        return self.results[key]

    def __len__(self):
        return len(self.results)

    def is_present(self):
        """
        Check whether the query returns any results.

        Returns:
            Boolean indicating whether the query contains any results.
        """
        return bool(self.results)

    present = property(is_present)

    @property
    def first(self):
        """
        Return a Query that selects only the first element of this Query.
        If no elements are available, returns a query with no results.

        Example usage:

        .. code:: python

            >> q = Query(lambda: list(range(5)))
            >> q.first.results
            [0]

        Returns:
            Query
        """
        def _transform(xs):  # pylint: disable=missing-docstring, invalid-name
            try:
                return [six.next(iter(xs))]
            except StopIteration:
                return []

        return self.transform(_transform, 'first')

    def nth(self, index):
        """
        Return a query that selects the element at `index` (starts from 0).
        If no elements are available, returns a query with no results.

        Example usage:

        .. code:: python

            >> q = Query(lambda: list(range(5)))
            >> q.nth(2).results
            [2]

        Args:
            index (int): The index of the element to select (starts from 0)

        Returns:
            Query
        """
        def _transform(xs):  # pylint: disable=missing-docstring, invalid-name
            try:
                return [next(islice(iter(xs), index, None))]

            # Gracefully handle (a) running out of elements, and (b) negative indices
            except (StopIteration, ValueError):
                return []

        return self.transform(_transform, 'nth')

    def __repr__(self):
        return u".".join([self.desc] + self.desc_stack)


class QueryableQuery(Query):
    """
    A Query that operates on a WebDriver queryable object (a browser or an element).
    """
    def __init__(self, browser, queryable, **kwargs):
        """
        Generate a query over a queryable.

        Args:
            browser (WebDriver): A Selenium-controlled browser.
            queryable (WebDriver or WebElement): A Selenium-controlled queryable.

        Keyword Args:
            css (str): A CSS selector.
            xpath (str): An XPath selector.
            class (str): A css class name.
            id (str): An element id.
            link (str): Link text.
            name (str): An element name
            partial_link (str): Partial link text
            tag (str): A tag name

        Returns:
            QueryableQuery

        Raises:
            TypeError: The query must be passed either a CSS or XPath selector, but not both.
        """
        if len(kwargs) > 1:
            raise TypeError('QueryableQuery() takes at most 1 keyword argument.')

        if not kwargs:
            raise TypeError('Must pass a query keyword argument to QueryableQuery().')

        query_name, query_value = kwargs.popitem()

        if query_name not in QUERY_TYPES:
            raise TypeError('{} is not a supported query type for QueryableQuery()'.format(query_name))

        def query_fn():  # pylint: disable=missing-docstring
            return queryable.find_elements(QUERY_TYPES[query_name], query_value)

        super(QueryableQuery, self).__init__(
            query_fn,
            desc=u"QueryableQuery({}={!r})".format(query_name, query_value),
        )
        self.queryable = queryable
        self.browser = browser

    def q(self, **kwargs):  # pylint: disable=invalid-name
        """
        Construct a subquery from this one.

        Example usages:

        .. code:: python

            self.q(css="div.foo").q(tag='button').first.click()
            self.q(xpath="/foo/bar").text

        Keyword Args:
            css (str): A CSS selector.
            xpath (str): An XPath selector.
            class (str): A css class name.
            id (str): An element id.
            link (str): Link text.
            name (str): An element name
            partial_link (str): Partial link text
            tag (str): A tag name

        Returns:
            QueryableQuery
        """
        if len(kwargs) > 1:
            raise TypeError('q() takes at most 1 keyword argument.')

        if not kwargs:
            raise TypeError('Must pass a query keyword argument to q().')

        query_name, query_value = kwargs.popitem()

        if query_name not in QUERY_TYPES:
            raise TypeError('{} is not a supported query type for q()'.format(query_name))

        return self.flat_map(lambda ele: ele.find_elements(QUERY_TYPES[query_name], query_value))

    def attrs(self, attribute_name):
        """
        Retrieve HTML attribute values from the elements matched by the query.

        Example usage:

        .. code:: python

            # Assume that the query matches html elements:
            # <div class="foo"> and <div class="bar">
            >> q.attrs('class')
            ['foo', 'bar']

        Args:
            attribute_name (str): The name of the attribute values to retrieve.

        Returns:
            A list of attribute values for `attribute_name`.
        """
        desc = 'attrs({!r})'.format(attribute_name)
        return self.map(lambda el: el.get_attribute(attribute_name), desc).results

    @property
    def text(self):
        """
        Retrieve text from each matched element.

        Example usage:

        .. code:: python

            # Assume that the query matches html elements:
            # <div>Foo</div> and <div>Bar</div>
            >> q.text
            ['Foo', 'Bar']

        Returns:
            The text of each element matched by the query.
        """
        return self.map(lambda el: el.text, 'text').results

    @property
    def html(self):
        """
        Retrieve the inner HTML of each element matched by the query.

        Example usage:

        .. code:: python

            # Assume that the query matches html elements:
            # <div><span>Foo</span></div> and <div>Bar</div>
            >> q.html
            ['<span>Foo</span>', 'Bar']

        Returns:
            The inner HTML for each element matched by the query.
        """
        return self.map(lambda el: el.get_attribute('innerHTML'), 'html').results

    @property
    def selected(self):
        """
        Check whether all the matched elements are selected.

        Returns:
            bool
        """
        query_results = self.map(lambda el: el.is_selected(), 'selected').results
        if query_results:
            return all(query_results)
        else:
            return False

    @property
    def visible(self):
        """
        Check whether all matched elements are visible.

        Returns:
            bool
        """
        query_results = self.map(lambda el: el.is_displayed(), 'visible').results
        if query_results:
            return all(query_results)
        else:
            return False

    @property
    def invisible(self):
        """
        Check whether all matched elements are present, but not visible.

        Returns:
            bool
        """
        return self.present and not self.visible

    def is_focused(self):
        """
        Checks that *at least one* matched element is focused. More
        specifically, it checks whether the element is document.activeElement.
        If no matching element is focused, this returns `False`.

        Returns:
            bool
        """
        active_el = self.browser.execute_script("return document.activeElement")
        query_results = self.map(lambda el: el == active_el, 'focused').results

        if query_results:
            return any(query_results)
        else:
            return False

    focused = property(is_focused)

    def click(self):
        """
        Click each matched element.

        Example usage:

        .. code:: python

            # Click the first element matched by the query
            q.first.click()

        Returns:
            None
        """
        self.map(lambda el: ActionChains(self.browser).move_to_element(el).click(el).perform(), 'click()').execute()

    def fill(self, text):
        """
        Set the text value of each matched element to `text`.

        Example usage:

        .. code:: python

            # Set the text of the first element matched by the query to "Foo"
            q.first.fill('Foo')

        Args:
            text (str): The text used to fill the element (usually a text field or text area).

        Returns:
            None
        """
        def _fill(elem):  # pylint: disable=missing-docstring
            elem.clear()
            elem.send_keys(text)

        self.map(_fill, 'fill({!r})'.format(text)).execute()


class BrowserQuery(QueryableQuery):
    def __init__(self, browser, **kwargs):
        super(BrowserQuery, self).__init__(browser, browser, **kwargs)