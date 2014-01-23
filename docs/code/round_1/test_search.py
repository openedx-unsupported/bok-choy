import unittest
from bok_choy.web_app_test import WebAppTest
from pages import GitHubSearchPage


class TestGitHub(WebAppTest):
    """
    Tests for the GitHub site.
    """

    def test_page_existence(self):
        """
        Make sure that the page is accessible.
        """
        GitHubSearchPage(self.browser).visit()


if __name__ == '__main__':
    unittest.main()
