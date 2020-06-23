"""
Tests of the ``bok_choy.query`` module
"""

from unittest import TestCase

from mock import Mock
from selenium.common.exceptions import WebDriverException
from bok_choy.query import Query, BrowserQuery


class TestQuery(TestCase):
    """
    Tests of the ``Query`` class
    """
    def setUp(self):
        super(TestQuery, self).setUp()
        self.query = Query(lambda: list(range(5)))

    def test_initial_identify(self):
        assert self.query.results == [0, 1, 2, 3, 4]

    def test_replace(self):
        clone = self.query.replace(seed_fn=lambda: list(range(3)))
        assert id(self.query) != id(clone)
        assert clone.results == [0, 1, 2]
        assert self.query.results == [0, 1, 2, 3, 4]

        clone2 = self.query.replace(transforms=[lambda xs: (x + 1 for x in xs)])
        assert id(self.query) != id(clone2)
        assert clone2.results == [1, 2, 3, 4, 5]
        assert self.query.results == [0, 1, 2, 3, 4]

        with self.assertRaises(TypeError):
            self.query.replace(foo='bar')

    def test_transform(self):
        transformed = self.query.transform(lambda xs: (x + 1 for x in xs))
        assert id(self.query) != id(transformed)
        assert transformed.results == [1, 2, 3, 4, 5]
        assert self.query.results == [0, 1, 2, 3, 4]

    def test_transforms_stack(self):
        transformed = self.query.transform(
            lambda xs: (x + 1 for x in xs)
        ).transform(
            lambda xs: (x * 2 for x in xs)
        )

        assert id(self.query) != id(transformed)
        assert transformed.results == [2, 4, 6, 8, 10]
        assert self.query.results == [0, 1, 2, 3, 4]

    def test_map(self):
        mapped = self.query.map(lambda x: x + 1)
        transformed = self.query.transform(lambda xs: (x + 1 for x in xs))
        assert id(self.query) != id(mapped)
        assert transformed.results == mapped.results

    def test_filter(self):
        filtered = self.query.filter(lambda x: x % 2 == 0)
        assert id(self.query) != id(filtered)
        assert filtered.results == [0, 2, 4]

    def test_filter_shortcut(self):
        mapped = self.query.map(lambda x: Mock(text=str(x)))
        filtered = mapped.filter(text="3")
        assert len(filtered) == 1
        assert filtered[0].text == mapped[3].text

    def test_filter_invalid_args(self):

        # Both filter func and params
        with self.assertRaises(TypeError):
            self.query.filter(lambda x: x % 2 == 0, text="3")

        # Neither filter func nor params
        with self.assertRaises(TypeError):
            self.query.filter()

    def test_retry_on_error(self):
        seed = Mock()
        seed.side_effect = [WebDriverException, ["success"]]
        self.assertEqual(["success"], Query(seed_fn=seed).results)

    def test_length(self):
        assert len(self.query) == 5
        assert len(self.query.filter(lambda x: x % 2 == 0)) == 3

    def test_present(self):
        self.assertTrue(self.query.present)
        self.assertFalse(self.query.filter(lambda x: x > 10).present)

    def test_getitem(self):
        assert self.query[3] == 3
        assert self.query.filter(lambda x: x % 2 == 0)[1] == 2

    def test_repr(self):
        assert repr(self.query) == u"Query(<lambda>)"

        def integers():
            """
            Return the first 100 integers
            """
            return list(range(100))

        assert repr(Query(integers)) == u"Query(integers)"

        assert repr(self.query.map(lambda x: x + 1)) == u"Query(<lambda>).map(<lambda>)"
        assert repr(self.query.map(lambda x: x + 1, 'x + 1')) == u"Query(<lambda>).map(x + 1)"
        self.assertEqual(
            u"Query(<lambda>).map(x + 1).filter(<lambda>)",
            repr(self.query.map(lambda x: x + 1, 'x + 1').filter(lambda x: x > 2))
        )
        self.assertEqual(
            u"Query(<lambda>).transform(<lambda>)",
            repr(self.query.transform(lambda xs: iter(xs).next(0)))
        )
        self.assertEqual(
            u"Query(<lambda>).filter(text='foo')",
            repr(self.query.filter(text='foo'))
        )

    def test_first(self):
        query = Query(lambda: list(range(2)))
        self.assertEqual([0], query.first.results)
        self.assertEqual([0], query.first.first.results)

    def test_first_no_results(self):
        query = Query(lambda: [])
        self.assertEqual([], query.first.results)

    def test_nth(self):
        query = Query(lambda: list(range(2)))
        self.assertEqual([], query.nth(-1).results)
        self.assertEqual([0], query.nth(0).results)
        self.assertEqual([1], query.nth(1).results)
        self.assertEqual([], query.nth(2).results)


class TestBrowserQuery(TestCase):
    """
    Tests of the ``BrowserQuery`` class.
    """
    def setUp(self):
        super(TestBrowserQuery, self).setUp()
        self.browser = Mock(
            find_elements_by_css_selector=Mock(return_value=list(range(3))),
            find_elements_by_xpath=Mock(return_value=list(range(10)))
        )

    def test_error_cases(self):
        with self.assertRaises(TypeError):
            BrowserQuery(self.browser, css='foo', xpath='bar')

        with self.assertRaises(TypeError):
            BrowserQuery(self.browser)

        with self.assertRaises(TypeError):
            BrowserQuery(self.browser, foo='bar')

    def test_query_args(self):
        self.assertEqual(
            self.browser.find_elements_by_css_selector.return_value,
            BrowserQuery(self.browser, css='foo').results
        )
        self.assertEqual(
            self.browser.find_elements_by_xpath.return_value,
            BrowserQuery(self.browser, xpath='foo').results
        )

    def test_repr(self):
        assert repr(BrowserQuery(self.browser, css='foo')) == u"BrowserQuery(css='foo')"
        assert repr(BrowserQuery(self.browser, xpath='foo')) == u"BrowserQuery(xpath='foo')"
