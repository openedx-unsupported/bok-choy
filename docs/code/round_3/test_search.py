import unittest
from bok_choy.web_app_test import WebAppTest
from pages import GitHubSearchPage, GitHubSearchResultsPage

class TestGitHub(WebAppTest):
    """
    Tests for the GitHub site.
    """

    def setUp(self):
        """
        Instantiate the page object.
        """
        super(TestGitHub, self).setUp()
        self.github_search_page = GitHubSearchPage(self.browser)
        self.github_results_page = GitHubSearchResultsPage(self.browser)

    def test_page_existence(self):
        """
        Make sure that the page is accessible.
        """
        self.github_search_page.visit()

    def test_search(self):
        """
        Make sure that you can search for something.
        """
        self.github_search_page.visit().search_for_terms('user:edx repo:edx-platform')
        search_results = self.github_results_page.search_results
        print(self.github_results_page)
        assert 'edx/edx-platform' in search_results
        assert search_results[0] == 'edx/edx-platform'


if __name__ == '__main__':
    unittest.main()
