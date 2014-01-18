import unittest
from bok_choy.web_app_test import WebAppTest
from pages import GitHubSearchPage, GitHubSearchResultsPage

class TestGitHub(WebAppTest):
    """
    Tests for the GitHub site.
    """

    page_object_classes = [GitHubSearchPage, GitHubSearchResultsPage]

    def test_page_existence(self):
        """
        Make sure that the page is accessible.
        """
        self.ui.visit('github_search')

    def test_search(self):
        """
        Make sure that you can search for something.
        """
        self.ui.visit('github_search')
        self.ui['github_search'].search_for_terms('user:edx repo:edx-platform')
        search_results = self.ui['github_search_results'].search_results
        assert 'edx/edx-platform' in search_results
        assert search_results[0] == 'edx/edx-platform'


if __name__ == '__main__':
    unittest.main()
