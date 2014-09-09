# -*- coding: utf-8 -*-
from bok_choy.page_object import PageObject
import re


class GitHubSearchResultsPage(PageObject):
    """
    GitHub's search results page
    """

    url = None

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
        return self.q(css='ul.repo-list > li > h3.repo-list-name > a').text


class GitHubSearchPage(PageObject):
    """
    GitHub's search page
    """

    url = 'http://www.github.com/search'

    def is_browser_on_page(self):
        return self.q(css='button.button').is_present()

    def enter_search_terms(self, text):
        """
        Fill the text into the input field
        """
        self.q(css='#search_form > input[type="text"]').fill(text)

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


