"""
Tools for querying html inside a running browser.
"""

from copy import copy
from selenium.common.exceptions import WebDriverException, StaleElementReferenceException
from splinter.exceptions import ElementDoesNotExist
from collections import Sequence

from bok_choy.promise import Promise, fulfill


SUPPORTED_QUERY_TYPES = ['css', 'id', 'value', 'text', 'xpath']


class KeepWaiting(Exception):
    """
    Dummy exception to indicate that a check function wants to continue waiting.
    """
    pass


RETRY_EXCEPTIONS = (
    WebDriverException, StaleElementReferenceException,
    ElementDoesNotExist, KeepWaiting
)


def no_error(func):
    """
    Decorator to create a `Promise` check function that is satisfied
    only when `func()` executes successfully.
    """
    def _inner(*args, **kwargs):
        try:
            return_val = func(*args, **kwargs)
        except RETRY_EXCEPTIONS:
            return (False, None)
        else:
            return (True, return_val)

    return _inner


class Query(Sequence):
    """
    This represents a general interface for an object that produces values
    (by calling `seed_fn`), and then transforms them arbitrarily (using the
    contents of `transforms').
    """
    def __init__(self, seed_fn, msg_base=None):
        if msg_base is None:
            msg_base = u'Query({})'.format(seed_fn.__name__)

        self.seed_fn = seed_fn
        self.transforms = []
        self.msg_stack = []
        self.msg_base = msg_base
        self._results = None

    def replace(self, **kwargs):
        """
        Return a copy of this `Query`, but with attributes specified
        as keyword arguments replaced by the keyword values.
        """
        clone = copy(self)
        clone.reset()

        clone.transforms = list(clone.transforms)
        for key, value in kwargs.items():
            if not hasattr(clone, key):
                raise TypeError('replace() got an unexpected keyword argument {!r}'.format(key))

            setattr(clone, key, value)
        return clone

    def transform(self, transform, msg=None):
        """
        Return a copy of this query, transformed by `transform`.

        Args:
            transform: A function that takes an iterable of values, and yields new values
            msg (str): A description of what this transform is doing (like `transform(add_one)`
        """
        if msg is None:
            msg = u'transform({})'.format(transform.__name__)

        return self.replace(
            transforms=self.transforms + [transform],
            msg_stack=self.msg_stack + [msg]
        )

    def map(self, map_fn, msg=None):
        """
        Return a copy of this query, with the values mapped through `map_fn`.

        Args:
            map_fn: A function that takes a single argument, and returns a new valu
            msg (str): A description of what map_fn is doing (if not supplied, will be the
                `__name__` of `map_fn`).
        """
        if msg is None:
            msg = map_fn.__name__

        return self.transform(lambda xs: (map_fn(x) for x in xs), u'map({})'.format(msg))

    def filter(self, filter_fn=None, msg=None, **kwargs):
        """
        Return a copy of this query, with some values removed.

        Args:
            filter_fn: If set, this must be a function that takes one argument,
                and returns True or False
            msg: A description of what filter_fn is doing (if not supplied, will be the
                `__name__` of `filter_fn`)
            kwargs: If any keyword arguments are set, then only elements
                of the query whose attributes match the values specified by the
                keyword arguments will be returned.
        """
        if filter_fn is not None and kwargs:
            raise TypeError('Must supply either a filter_fn or attribute filter parameters to filter(), but not both.')
        if filter_fn is None and not kwargs:
            raise TypeError('Must supply one of filter_fn or one or more attribute filter parameters to filter().')

        if kwargs:
            def filter_fn(elem):
                return all(
                    getattr(elem, filter_key) == filter_value
                    for filter_key, filter_value
                    in kwargs.items()
                )

            msg = u", ".join([u"{}={!r}" for key, value in kwargs.items()])

        if msg is None:
            msg = filter_fn.__name__

        return self.transform(lambda xs: (x for x in xs if filter_fn(x)), u'filter({})'.format(msg))

    def _execute(self):
        data = self.seed_fn()
        for transform in self.transforms:
            data = transform(data)
        return list(data)

    def execute(self, try_limit=5, try_interval=0.5, timeout=30):
        """
        Execute this query, retrying based on the supplied parameters.

        Args:
            try_limit (int): The number of times to retry the query.
            try_interval (float): The number of seconds to wait between each try.
            timeout (float): The maximum number of seconds to spend retrying.
        """
        return fulfill(Promise(
            no_error(self._execute),
            u"Executing {!r}".format(self),
            try_limit=try_limit,
            try_interval=try_interval,
            timeout=timeout,
        ))

    @property
    def results(self):
        """
        A list of the results of the query. Will be cached.
        """
        if self._results is None:
            self._results = self.execute()
        return self._results

    def reset(self):
        """
        Reset the cache of query results.
        """
        self._results = None

    def __getitem__(self, key):
        return self.results[key]

    def __len__(self):
        return len(self.results)

    @property
    def present(self):
        """
        True if the query returns any elements.
        """
        return bool(self.results)

    @property
    def text(self):
        """
        Return the text attributes of each of the results of this Query.
        """
        return self.map(lambda el: el.text, 'text').results

    @property
    def html(self):
        """
        Return the html attributes of each of the results of this Query.
        """
        return self.map(lambda el: el.html).results

    @property
    def value(self):
        """
        Return the value attributes of each of the results of this Query.
        """
        return self.map(lambda el: el.value, 'value').results

    @property
    def first(self):
        """
        Return a Query that only selects the first element of this Query.
        """
        return self.transform(lambda xs: [iter(xs).next()], 'first')

    def click(self):
        """
        Call `.click` on all elements selected by this Query, and
        return the elements unchanged.
        """
        self.map(lambda el: el.click(), 'click()').execute()

    @property
    def selected(self):
        """
        Call `.selected` on all elements selected by this Query.
        """
        return self.map(lambda el: el.selected, 'selected')

    def fill(self, text):
        """
        Call `.fill(text)` on all elements selected by this Query.
        """
        return self.map(lambda el: el.fill(text), 'fill({!r})'.format(text)).execute()

    def __repr__(self):
        return u".".join([self.msg_base] + self.msg_stack)


class BrowserQuery(Query):
    """
    A Query that operates on a browser.
    """
    def __init__(self, browser, **kwargs):
        """
        Generate a query over a browser.

        Args:
            browser: A :class:`splinter.browser.Browser`.
            kwargs: Only a single keyword argument may be passed. It is used to
                select a `find_by_*` method from the browser to use as the `seed_fn`.
                The keyword value is used as the single argument to the `find_by_*` method.
        """
        if len(kwargs) > 1:
            raise TypeError('BrowserQuery() takes at most 1 keyword argument.')

        if not kwargs:
            raise TypeError('Must pass a query keyword argument to BrowserQuery().')

        query, value = kwargs.items()[0]

        if query not in SUPPORTED_QUERY_TYPES:
            raise TypeError('{} is not a supported query type for BrowserQuery()'.format(query))

        def query_fn():
            return getattr(browser, 'find_by_{}'.format(query))(value)

        super(BrowserQuery, self).__init__(
            query_fn,
            msg_base=u"BrowserQuery({}={!r})".format(query, value),
        )
        self.browser = browser


class SubQuery(Query):
    """
    A Query that is late-bound to an element, so that it can be used as an
    argument to :meth:`.Query.map` or :meth:`.Query.filter`.
    """

    def __init__(self, **kwargs):
        """
        Generate a subquery.

        Args:
            kwargs: Only a single keyword argument may be passed. It is used to
                select a `find_by_*` method from the bound element to use as the `seed_fn`.
                The keyword value is used as the single argument to the `find_by_*` method.
        """
        if len(kwargs) > 1:
            raise TypeError('SubQuery() takes at most 1 keyword argument.')

        if not kwargs:
            raise TypeError('Must supply at least one query parameter to SubQuery().')

        self.query_name, self.query_value = kwargs.items()[0]

        if self.query_name not in SUPPORTED_QUERY_TYPES:
            raise TypeError('{} is not a supported query type for SubQuery()'.format(self.query_name))

        super(SubQuery, self).__init__(
            None,
            msg_base=u"SubQuery({}={!r})".format(self.query_name, self.query_value)
        )

    def execute(self):
        # Don't do separate retries on the SubQuery portion of a Query
        return self._execute()

    def __call__(self, elem):
        """
        Return a copy of this SubQuery, bound to the supplied element `elem`.
        """
        def seed_fn():
            return getattr(elem, 'find_by_{}'.format(self.query_name))(self.query_value)

        return self.replace(seed_fn=seed_fn, msg_base='SubQuery({})').results

    @property
    def __name__(self):
        return repr(self)
