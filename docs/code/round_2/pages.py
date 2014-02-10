# -*- coding: utf-8 -*-
import re
from bok_choy.page_object import PageObject


class GitHubSearchResultsPage(PageObject):
    """
    GitHub's search results page
    """

    # You do not navigate to this page directly
    url = None

    def is_browser_on_page(self):
        # This should be something like: u'Search · foo bar · GitHub'
        title = self.browser.title
        matches = re.match(u'^Search .+$', title)
        return matches is not None


class GitHubSearchPage(PageObject):
    """
    GitHub's search page
    """

    url = 'http://www.github.com/search'

    def is_browser_on_page(self):
        return 'code search' in self.browser.title.lower()

    def enter_search_terms(self, text):
        """
        Fill the text into the input field
        """
        
        self.q(css='input#js-command-bar-field').fill(text)

    def search(self):
        """
        Click on the Search button and wait for the
        results page to be displayed
        """
        self.q(css='button.button').click()
        GitHubSearchResultsPage(self.browser).wait_for_page()

    def search_for_terms(self, text):
        """
        Fill in the search terms and click the
        Search button
        """
        self.enter_search_terms(text)
        self.search()
