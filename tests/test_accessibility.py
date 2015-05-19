"""
Test accessibility auditing.
"""
import os

from mock import patch

from bok_choy.web_app_test import WebAppTest
from bok_choy.page_object import AccessibilityError

from .pages import AccessibilityPage


class NoAccessibilityTest(WebAppTest):
    """
    Test unsupported accessibility audit configuration.
    """
    @patch.dict(os.environ, {'SELENIUM_BROWSER': 'firefox'})
    def test_axs_audit_firefox(self):
        page = AccessibilityPage(self.browser).visit()
        with self.assertRaises(NotImplementedError):
            page.do_axs_audit()


class AccessibilityTest(WebAppTest):
    """
    Test accessibility audit integration.
    """
    @patch.dict(os.environ, {'SELENIUM_BROWSER': 'phantomjs'})
    def setUp(self):
        super(AccessibilityTest, self).setUp()
        self.ax_aria_04_errors = u'{}{}{}{}'.format(
            'Error: AX_ARIA_04 ',
            '(ARIA state and property values must be valid) failed on the following ',
            'element:\n',
            '#AX_ARIA_04_bad')
        self.ax_aria_01_errors = u'{}{}{}{}{}{}'.format(
            'Error: AX_ARIA_01 ',
            '(Elements with ARIA roles must use a valid, non-abstract ARIA role) failed on the following ',
            'elements (1 - 2 of 2):\n',
            '#AX_ARIA_01_not_a_role\n#AX_ARIA_01_empty_role\n',
            'See https://github.com/GoogleChrome/accessibility-developer-tools/wiki/Audit-Rules',
            '#-ax_aria_01--elements-with-aria-roles-must-use-a-valid-non-abstract-aria-role for more information.')

    @patch('tests.pages.AccessibilityPage.axs_audit_rules_to_run')
    def test_axs_audit_no_rules(self, mock_rules):
        page = AccessibilityPage(self.browser)
        mock_rules.return_value = None
        page.visit()
        report = page.do_axs_audit()
        self.assertIsNone(report)

        # Make sure the mock was really called
        mock_rules.assert_called_once_with()

    def test_axs_audit_default_rules(self):
        # Default page object definition is to check all rules
        page = AccessibilityPage(self.browser)
        page.visit()
        report = page.do_axs_audit()

        # There was one page in this session
        self.assertEqual(1, len(report))
        result = report[0]

        # When checking all rules, results are 2 errors and 0 warnings
        self.assertEqual(2, len(result.errors))
        self.assertEqual(result.errors[0], self.ax_aria_04_errors)
        self.assertEqual(result.errors[1], self.ax_aria_01_errors)

        self.assertEqual(0, len(result.warnings))

    @patch('tests.pages.AccessibilityPage.axs_scope')
    def test_axs_audit_limit_scope(self, mock_scope):
        # Limit the scope to the div with AX_ARIA_04 violations
        mock_scope.return_value = 'document.querySelector("#limit_scope")'
        page = AccessibilityPage(self.browser)
        page.visit()
        report = page.do_axs_audit()

        mock_scope.assert_called_once_with()

        # There was one page in this session
        self.assertEqual(1, len(report))
        result = report[0]

        self.assertEqual(1, len(result.errors))
        self.assertEqual(result.errors[0], self.ax_aria_04_errors)

        self.assertEqual(0, len(result.warnings))

    @patch('tests.pages.AccessibilityPage.axs_audit_rules_to_run')
    def test_axs_audit_limit_rules(self, mock_rules):
        # Limit the rules checked to AX_ARIA_01
        mock_rules.return_value = ['badAriaRole']
        page = AccessibilityPage(self.browser)
        page.visit()
        report = page.do_axs_audit()

        mock_rules.assert_called_once_with()

        # There was one page in this session
        self.assertEqual(1, len(report))
        result = report[0]

        self.assertEqual(1, len(result.errors))
        self.assertEqual(result.errors[0], self.ax_aria_01_errors)

        self.assertEqual(0, len(result.warnings))


class TestVerifyAccessibilityFlagTest(WebAppTest):
    """
    Test accessibility audit integration that happens implicitly on
    a call that invokes wait_for_page.
    """
    @patch.dict(os.environ, {'SELENIUM_BROWSER': 'phantomjs'})
    def setUp(self):
        super(TestVerifyAccessibilityFlagTest, self).setUp()

    @patch.dict(os.environ, {'VERIFY_ACCESSIBILITY': 'True'})
    def test_axs_audit_check_on_visit(self):
        page = AccessibilityPage(self.browser)
        with self.assertRaises(AccessibilityError):
            page.visit()

    @patch.dict(os.environ, {'VERIFY_ACCESSIBILITY': 'False'})
    def test_axs_audit_no_checks(self):
        page = AccessibilityPage(self.browser)
        page.visit()
        self.assertTrue(page.is_browser_on_page())
