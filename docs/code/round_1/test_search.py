import unittest
from bok_choy.web_app_test import WebAppTest
from pages import GitHubSearchPage

class TestGitHub(WebAppTest):
    """
    Tests for the GitHub site.
    """

    page_object_classes = [GitHubSearchPage]

    def test_page_existence(self):
        """
        Make sure that the page is accessible.
        """
        self.ui.visit('github_search')


if __name__ == '__main__':
    unittest.main()
