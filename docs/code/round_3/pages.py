# -*- coding: utf-8 -*-
from bok_choy.page_object import PageObject
import re


class GitHubSearchPage(PageObject):
    """
    GitHub's search page
    """

    name = 'github_search'

    def url(self):
        return 'http://www.github.com/search'

    def is_browser_on_page(self):
        return 'code search' in self.browser.title.lower()

    def enter_search_terms(self, text):
        """
        Fill the text into the input field
        """
        self.css_fill('input#js-command-bar-field', text)

    def search(self):
        """
        Click on the Search button and wait for the
        results page to be displayed
        """
        self.css_click('button.button')
        self.ui.wait_for_page('github_search_results')

    def search_for_terms(self, text):
        """
        Fill in the search terms and click the
        Search button
        """
        self.enter_search_terms(text)
        self.search()


class GitHubSearchResultsPage(PageObject):
    """
    GitHub's search results page
    """

    name = 'github_search_results'

    def url(self, **kwargs):
        """
        You do not navigate here directly
        """
        raise NotImplemented

    def is_browser_on_page(self):
        # This should be something like: u'Search · foo bar · GitHub'
        title = self.browser.title
        matches = re.match(u'^Search .+ GitHub$', title)
        return matches is not None

    @property
    def search_results(self):
        """
        Return a list of results returned from a search
        """
        return self.css_text('ul.repolist > li > h3.repolist-name > a')
