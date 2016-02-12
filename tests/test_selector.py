"""
Tests for retrieving values from the page using CSS selectors.
"""

from bok_choy.web_app_test import WebAppTest
from .pages import SelectorPage
from .pages import LongPage
from bok_choy.promise import BrokenPromise


class SelectorTest(WebAppTest):
    """
    Test retrieving values by CSS selector.
    """

    def setUp(self):
        super(SelectorTest, self).setUp()

        self.selector = SelectorPage(self.browser)
        self.selector.visit()

    def test_count(self):
        self.assertEquals(self.selector.num_divs, 4)

    def test_text(self):
        self.assertEquals(
            self.selector.div_text_list,
            ['Test div 1', 'Test div 2', 'Test div 3', 'Test div 4']
        )

    def test_value(self):
        self.assertEquals(
            self.selector.div_value_list,
            ['value 1', 'value 2', 'value 3', 'value 4']
        )

    def test_html(self):
        self.assertEquals(
            self.selector.div_html_list,
            ['Test div 1', 'Test div 2', 'Test div 3', 'Test div 4']
        )

    def test_is_present(self):
        self.assertTrue(self.selector.q(css='div#fixture').present)
        self.assertFalse(self.selector.q(css='div#not_present').present)

    def test_filtered_query(self):
        outer_id_list = self.selector.ids_of_outer_divs_with_inner_text('Match This')
        self.assertEquals(outer_id_list, ['o2', 'o3'])

    def test_filtered_query_no_match(self):
        outer_id_list = self.selector.ids_of_outer_divs_with_inner_text('This does not match anything')
        self.assertEquals(outer_id_list, [])


class ScrollTest(WebAppTest):
    """
    Test scrolling to element
    """

    def setUp(self):
        super(ScrollTest, self).setUp()

        self.long_page = LongPage(self.browser)
        self.long_page.visit()

    def test_scroll(self):
        self.assertEquals(self._get_window_position(), 0)
        self.long_page.scroll_to_element('#element_after_long_part')
        # Different browsers, CI systems, and resolutions may present the
        # element in varying locations. Use a greater-than instead of an equals.
        self.assertGreaterEqual(self._get_window_position(), 1900)

    def test_scroll_false_element(self):
        """
        When scroll_to_element is given a non-existent element, it should
        raise a BrokenPromise
        """
        with self.assertRaises(BrokenPromise):
            self.long_page.scroll_to_element('.foo', timeout=1)

    def _get_window_position(self):
        return self.browser.execute_script("return window.scrollY;")
