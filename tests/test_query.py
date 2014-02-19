from mock import Mock
from unittest import TestCase
from selenium.common.exceptions import WebDriverException

from bok_choy.query import Query, BrowserQuery


class TestQuery(TestCase):
    def setUp(self):
        self.query = Query(lambda: range(5))

    def test_initial_identify(self):
        self.assertEquals([0, 1, 2, 3, 4], self.query.results)

    def test_replace(self):
        clone = self.query.replace(seed_fn=lambda: range(3))
        self.assertNotEquals(id(clone), id(self.query))
        self.assertEquals([0, 1, 2], clone.results)
        self.assertEquals([0, 1, 2, 3, 4], self.query.results)

        clone2 = self.query.replace(transforms=[lambda xs: (x + 1 for x in xs)])
        self.assertNotEquals(id(clone2), id(self.query))
        self.assertEquals([1, 2, 3, 4, 5], clone2.results)
        self.assertEquals([0, 1, 2, 3, 4], self.query.results)

        with self.assertRaises(TypeError):
            self.query.replace(foo='bar')

    def test_transform(self):
        transformed = self.query.transform(lambda xs: (x + 1 for x in xs))
        self.assertNotEquals(id(transformed), id(self.query))
        self.assertEquals([1, 2, 3, 4, 5], transformed.results)
        self.assertEquals([0, 1, 2, 3, 4], self.query.results)

    def test_transforms_stack(self):
        transformed = self.query.transform(
            lambda xs: (x + 1 for x in xs)
        ).transform(
            lambda xs: (x * 2 for x in xs)
        )

        self.assertNotEquals(id(transformed), id(self.query))
        self.assertEquals([2, 4, 6, 8, 10], transformed.results)
        self.assertEquals([0, 1, 2, 3, 4], self.query.results)

    def test_map(self):
        mapped = self.query.map(lambda x: x + 1)
        transformed = self.query.transform(lambda xs: (x + 1 for x in xs))
        self.assertNotEquals(id(self.query), id(mapped))
        self.assertEquals(mapped.results, transformed.results)

    def test_filter(self):
        filtered = self.query.filter(lambda x: x % 2 == 0)
        self.assertNotEquals(id(self.query), id(filtered))
        self.assertEquals([0, 2, 4], filtered.results)

    def test_filter_shortcut(self):
        mapped = self.query.map(lambda x: Mock(text=str(x)))
        filtered = mapped.filter(text="3")
        self.assertEquals(1, len(filtered))
        self.assertEquals(mapped[3].text, filtered[0].text)

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
        self.assertEquals(5, len(self.query))
        self.assertEquals(3, len(self.query.filter(lambda x: x % 2 == 0)))

    def test_present(self):
        self.assertTrue(self.query.present)
        self.assertFalse(self.query.filter(lambda x: x > 10).present)

    def test_getitem(self):
        self.assertEquals(3, self.query[3])
        self.assertEquals(2, self.query.filter(lambda x: x % 2 == 0)[1])

    def test_repr(self):
        self.assertEquals(u"Query(<lambda>)", repr(self.query))

        def integers():
            return range(100)

        self.assertEquals(u"Query(integers)", repr(Query(integers)))

        self.assertEquals(u"Query(<lambda>).map(<lambda>)", repr(self.query.map(lambda x: x + 1)))
        self.assertEquals(u"Query(<lambda>).map(x + 1)", repr(self.query.map(lambda x: x + 1, 'x + 1')))
        self.assertEquals(
            u"Query(<lambda>).map(x + 1).filter(<lambda>)",
            repr(self.query.map(lambda x: x + 1, 'x + 1').filter(lambda x: x > 2))
        )
        self.assertEquals(
            u"Query(<lambda>).transform(<lambda>)",
            repr(self.query.transform(lambda xs: iter(xs).next(0)))
        )
        self.assertEquals(
            u"Query(<lambda>).filter(text='foo')",
            repr(self.query.filter(text='foo'))
        )

    def test_first(self):
        query = Query(lambda: range(2))
        self.assertEqual([0], query.first.results)
        self.assertEqual([0], query.first.first.results)

    def test_first_no_results(self):
        query = Query(lambda: [])
        self.assertEqual([], query.first.results)

    def test_nth(self):
        query = Query(lambda: range(2))
        self.assertEqual([], query.nth(-1).results)
        self.assertEqual([0], query.nth(0).results)
        self.assertEqual([1], query.nth(1).results)
        self.assertEqual([], query.nth(2).results)


class TestBrowserQuery(TestCase):
    def setUp(self):
        self.browser = Mock(
            find_elements_by_css_selector=Mock(return_value=range(3)),
            find_elements_by_xpath=Mock(return_value=range(10))
        )

    def test_error_cases(self):
        with self.assertRaises(TypeError):
            BrowserQuery(self.browser, css='foo', xpath='bar')

        with self.assertRaises(TypeError):
            BrowserQuery(self.browser)

        with self.assertRaises(TypeError):
            BrowserQuery(self.browser, foo='bar')

    def test_query_args(self):
        self.assertEquals(
            self.browser.find_elements_by_css_selector.return_value,
            BrowserQuery(self.browser, css='foo').results
        )
        self.assertEquals(
            self.browser.find_elements_by_xpath.return_value,
            BrowserQuery(self.browser, xpath='foo').results
        )

    def test_repr(self):
        self.assertEquals(u"BrowserQuery(css='foo')", repr(BrowserQuery(self.browser, css='foo')))
        self.assertEquals(u"BrowserQuery(xpath='foo')", repr(BrowserQuery(self.browser, xpath='foo')))
