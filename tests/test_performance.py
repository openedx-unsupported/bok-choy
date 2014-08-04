"""
Test basic performance report functionality
NOTE: To run these tests, browsermob-proxy-2.0-beta-9 must be installed

These aren't real unittests, just some sample scenarios.
"""

from bok_choy.performance import WebAppPerfReport, with_cache
from .pages import ButtonPage, TextFieldPage


class PerformanceReportTest(WebAppPerfReport):
    """
    Test basic functionality of single page performance reports.
    """
    def test_button_page_perf_no_cache(self):
        """
        Without the 'with_cached' decorator, the function will run
        only once and produce only one har file. Because it is run on a
        newly instantiated browser, it will have an empty cache to start.
        """
        self.new_page('ButtonPage')
        page = ButtonPage(self.browser)
        page.visit()
        self.save_har()

    @with_cache
    def test_button_page_perf_with_cache(self):
        """
        With the 'with_cached' decorator, the function will run
        twice during th 'test' and produce two har files. 

        The first time around, the browser will be newly instantiated so the cache
        will be empty to start. Note that this means if you navigate to multiple 
        pages during one test case, only the first page is guaranteed to have an 
        empty cache.

        The second time the function is called, the cache will have anything that was
        cached the first time.  The second har file name will have '_cached' appended
        to thename.
        """
        self.new_page('ButtonPage')
        page = ButtonPage(self.browser)
        page.visit()

        # The har file name defaults to the test_id, but you can pass an alternate name.
        self.save_har('ButtonPage1')

    @with_cache
    def test_multi_pages_one_har(self):
        """
        To save multiple pages to one har, just define multiple pages before saving the har.
        """
        self.new_page('ButtonPage')
        page = ButtonPage(self.browser)
        page.visit()

        self.new_page('TextFieldPage')
        page2 = TextFieldPage(self.browser)
        page2.visit()
        page2.enter_text('testing')

        self.save_har('ButtonPage_and_TextFieldPage')

    def test_multi_pages_multi_har(self):
        """
        This will save_har a har for the ButtonPage, then save a har file for
        the TextFieldPage.  Note that when the TextFieldPage is called, the browswer
        will have assets cached from the ButtonPage, so if there are common assets, the
        performance of the TextFieldPage will be affected.
        """
        self.new_page('ButtonPage')
        page = ButtonPage(self.browser)
        page.visit()
        self.save_har('ButtonPage2')

        self.new_page('TextFieldPage')
        page2 = TextFieldPage(self.browser)
        page2.visit()
        page2.enter_text('testing')
        self.save_har('TextFieldPage2')

    def test_caching_explicitly(self):
        """
        If you want to go to one page first to see how it affects the performance of
        a subsequent page without including the first in the har, you can do something
        like this.

        It will only capture data for the TextFieldPage.
        """
        page = ButtonPage(self.browser)
        page.visit()

        self.new_page('TextFieldPage')
        page2 = TextFieldPage(self.browser)
        page2.visit()
        page2.enter_text('testing')
        self.save_har()

    @with_cache
    def test_multi_pages_multi_har_with_cache(self):
        """
        This will save_har a har for the ButtonPage, then save a har file for
        the TextFieldPage.  Note that when the TextFieldPage is called, the browswer
        will have assets cached from the ButtonPage, so if there are common assets, the
        performance of the TextFieldPage will be affected.

        Including cached 
        """
        self.new_page('ButtonPage')
        page = ButtonPage(self.browser)
        page.visit()
        self.save_har()

        self.new_page('TextFieldPage')
        page2 = TextFieldPage(self.browser)
        page2.visit()
        page2.enter_text('testing')
        self.save_har()
