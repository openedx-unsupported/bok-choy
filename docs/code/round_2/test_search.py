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
        super().setUp()
        self.github_search_page = GitHubSearchPage(self.browser)

    def test_page_existence(self):
        """
        Make sure that the page is accessible.
        """
        self.github_search_page.visit()

    def test_search(self):
        """
        Make sure that you can search for something.
        """
        self.github_search_page.visit().search_for_terms('user:openedx repo:edx-platform')


if __name__ == '__main__':
    unittest.main()
