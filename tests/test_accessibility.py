"""
Test accessibility auditing.
"""
import os

from mock import patch, Mock
from requests import Response

from bok_choy.web_app_test import WebAppTest
from bok_choy.a11y.a11y_audit import AccessibilityError
from bok_choy.a11y.axs_ruleset import AxsAudit
from bok_choy.a11y.axe_core_ruleset import AxeCoreAudit
from bok_choy.promise import BrokenPromise
from .pages import AccessibilityPage


class NoAccessibilityTest(WebAppTest):
    """
    Test unsupported accessibility audit configuration.
    """
    @patch.dict(os.environ, {'SELENIUM_BROWSER': 'firefox'})
    def setUp(self):
        super(NoAccessibilityTest, self).setUp()

    def test_axs_audit_firefox(self):
        page = AccessibilityPage(self.browser).visit()
        with self.assertRaises(NotImplementedError):
            page.a11y_audit.do_audit()


class AccessibilityTest(WebAppTest):
    """
    Test general accessibility audit integration.
    """
    @patch.dict(os.environ, {'SELENIUM_BROWSER': 'phantomjs'})
    def setUp(self):
        super(AccessibilityTest, self).setUp()

    def test_failure_to_inject_script(self):
        page = AccessibilityPage(self.browser)
        page.visit()

        mock_response = Response()
        mock_response.json = Mock(return_value={"value": False})

        with patch('requests.post', return_value=mock_response):
            with self.assertRaises(RuntimeError):
                page.a11y_audit.do_audit()


@patch.dict(os.environ, {'BOKCHOY_A11Y_RULESET': 'google_axs'})
class AxsAccessibilityTest(WebAppTest):
    """
    Test axs ruleset accessibility audit integration.
    """
    @patch.dict(os.environ, {'SELENIUM_BROWSER': 'phantomjs'})
    def setUp(self):
        super(AxsAccessibilityTest, self).setUp()

        # Audit rule name is badAriaAttributeValue
        self.ax_aria_04_errors = u'{}{}{}{}'.format(
            'Error: AX_ARIA_04 ',
            '(ARIA state and property values must be valid) failed on the following ',
            'element:\n',
            '#AX_ARIA_04_bad')

        # Audit rule name is badAriaRole
        self.ax_aria_01_errors = u'{}{}{}{}{}{}'.format(
            'Error: AX_ARIA_01 ',
            '(Elements with ARIA roles must use a valid, non-abstract ARIA role) failed on the following ',
            'elements (1 - 2 of 2):\n',
            '#AX_ARIA_01_not_a_role\n#AX_ARIA_01_empty_role\n',
            'See https://github.com/GoogleChrome/accessibility-developer-tools/wiki/Audit-Rules',
            '#-ax_aria_01--elements-with-aria-roles-must-use-a-valid-non-abstract-aria-role for more information.')

        self.mock_audit_results = {
            'warnings_': [],
            'errors_': [
                'Error: AX_ARIA_00 (rule description) failed on:\n#element_id',
            ]
        }

    def test_axs_missing_rules_file(self):
        page = AccessibilityPage(self.browser)
        page.a11y_audit.config.set_rules_file("nonexistent_file")
        page.visit()
        with self.assertRaises(RuntimeError):
            report = page.a11y_audit.do_audit()

    def test_axs_audit_no_rules(self):
        page = AccessibilityPage(self.browser)
        page.a11y_audit.config.set_rules(None)
        page.visit()
        report = page.a11y_audit.do_audit()
        self.assertIsNone(report)

    def test_axs_audit_default_rules(self):
        # Default page object definition is to check all rules
        page = AccessibilityPage(self.browser)
        page.visit()
        report = page.a11y_audit.do_audit()

        # There was one page in this session
        self.assertEqual(1, len(report))
        result = report[0]

        # When checking all rules, results are 2 errors and 1 warnings
        self.assertEqual(2, len(result.errors))
        self.assertEqual(result.errors[0], self.ax_aria_04_errors)
        self.assertEqual(result.errors[1], self.ax_aria_01_errors)

        self.assertEqual(1, len(result.warnings))

    def test_axs_audit_include_scope(self):
        # Limit the scope to the div with AX_ARIA_04 violations
        page = AccessibilityPage(self.browser)
        page.a11y_audit.config.set_scope(['#limit_scope'])
        page.visit()
        report = page.a11y_audit.do_audit()

        # There was one page in this session
        self.assertEqual(1, len(report))
        result = report[0]

        self.assertEqual(1, len(result.errors))
        self.assertEqual(result.errors[0], self.ax_aria_04_errors)

        self.assertEqual(0, len(result.warnings))

    def test_axs_audit_exclude_scope(self):
        # Limit the scope to the div with AX_ARIA_04 violations
        page = AccessibilityPage(self.browser)
        with self.assertRaises(NotImplementedError):
            page.a11y_audit.config.set_scope(exclude='')

    def test_axs_audit_limit_rules(self):
        page = AccessibilityPage(self.browser)

        # Limit the rules checked to AX_ARIA_01
        page.a11y_audit.config.set_rules(['badAriaRole'])

        page.visit()
        report = page.a11y_audit.do_audit()

        # There was one page in this session
        self.assertEqual(1, len(report))
        result = report[0]

        self.assertEqual(1, len(result.errors))
        self.assertEqual(result.errors[0], self.ax_aria_01_errors)

        self.assertEqual(0, len(result.warnings))

    def test_axs_audit_run_multiple_rules(self):
        page = AccessibilityPage(self.browser)
        page.a11y_audit.config.set_rules(
            ['badAriaRole', 'badAriaAttributeValue'])
        page.visit()
        report = page.a11y_audit.do_audit()

        # There was one page in this session
        self.assertEqual(1, len(report))
        result = report[0]

        # It is expected that both rules will be reported.
        self.assertEqual(2, len(result.errors))
        self.assertIn(self.ax_aria_01_errors, result.errors)
        self.assertIn(self.ax_aria_04_errors, result.errors)

        self.assertEqual(0, len(result.warnings))

    def test_axs_audit_ignore_rule(self):
        page = AccessibilityPage(self.browser)

        # Ignore the rule AX_ARIA_01. For this test, that means the only rule
        # to result in an error should be AX_ARIA_04.
        page.a11y_audit.config.set_rules(['badAriaRole'], ignore=True)

        page.visit()
        report = page.a11y_audit.do_audit()

        # There was one page in this session
        self.assertEqual(1, len(report))
        result = report[0]

        self.assertEqual(1, len(result.errors))
        self.assertEqual(result.errors[0], self.ax_aria_04_errors)

        self.assertEqual(1, len(result.warnings))

    def test_axs_audit_ignore_multiple_rules(self):
        page = AccessibilityPage(self.browser)
        # Ignore multiple rules. In this test, we are explicitly ignoring each.
        page.a11y_audit.config.set_rules(
            ['badAriaRole', 'badAriaAttributeValue'],
            ignore=True
        )

        page.visit()
        report = page.a11y_audit.do_audit()

        # There was one page in this session
        self.assertEqual(1, len(report))
        result = report[0]

        self.assertEqual(0, len(result.errors))
        self.assertEqual(1, len(result.warnings))

    def test_axs_audit_ignore_1_and_run_1(self):
        page = AccessibilityPage(self.browser)
        page.a11y_audit.config.set_rules(['badAriaAttributeValue'])
        page.a11y_audit.config.set_rules(['badAriaRole'], ignore=True)
        page.visit()
        report = page.a11y_audit.do_audit()

        # There was one page in this session
        self.assertEqual(1, len(report))
        result = report[0]

        # It is expected that the badAriaRole error would be ignored because it
        # is in rules_to_ignore, but the rule badAriaAttributeValue
        # should still be reported.
        self.assertEqual(1, len(result.errors))
        self.assertEqual(result.errors[0], self.ax_aria_04_errors)

        self.assertEqual(0, len(result.warnings))

    def test_axs_audit_ignore_and_run_same_rule(self):
        page = AccessibilityPage(self.browser)
        page.a11y_audit.config.set_rules(['badAriaRole'])
        page.a11y_audit.config.set_rules(['badAriaRole'], ignore=True)

        page.visit()
        report = page.a11y_audit.do_audit()

        # There was one page in this session
        self.assertEqual(1, len(report))
        result = report[0]

        # `rules_to_ignore` take precedence over `rules_to_run`. This is the
        # default behavior of the google accessibility tool we are using.
        # It is expected that the badAriaRole error would be ignored because it
        # is in both rules_to_run and rules_to_ignore.
        # Because no other rules were specified in rules_to_run,
        # there should be no errors reported.
        self.assertEqual(0, len(result.errors))

    def test_axs_audit_ignore_1_and_run_2(self):
        page = AccessibilityPage(self.browser)
        page.a11y_audit.config.set_rules(
            ['badAriaRole', 'badAriaAttributeValue'])
        page.a11y_audit.config.set_rules(['badAriaRole'], ignore=True)

        page.visit()
        report = page.a11y_audit.do_audit()

        # There was one page in this session
        self.assertEqual(1, len(report))
        result = report[0]

        # It is expected that the badAriaRole error would be ignored because it
        # is in both rules_to_run and rules_to_ignore, but
        # the rule badAriaAttributeValue should be reported.
        self.assertEqual(1, len(result.errors))
        self.assertEqual(result.errors[0], self.ax_aria_04_errors)

        self.assertEqual(0, len(result.warnings))

    def test_axs_audit_ignore_0_and_run_2(self):
        page = AccessibilityPage(self.browser)
        page.a11y_audit.config.set_rules(
            ['badAriaRole', 'badAriaAttributeValue'])
        page.a11y_audit.config.set_rules([], ignore=True)

        page.visit()
        report = page.a11y_audit.do_audit()

        # There was one page in this session
        self.assertEqual(1, len(report))
        result = report[0]

        # It is expected that no rules will be ignored because we have set
        # rules_to_ignore to [], which translates to 'ingore none'.
        self.assertEqual(2, len(result.errors))
        self.assertIn(self.ax_aria_01_errors, result.errors)
        self.assertIn(self.ax_aria_04_errors, result.errors)
        self.assertEqual(0, len(result.warnings))

    def test_axs_audit_ignore_0_and_run_all(self):
        page = AccessibilityPage(self.browser)
        page.a11y_audit.config.set_rules([])
        page.a11y_audit.config.set_rules([], ignore=True)
        page.visit()
        report = page.a11y_audit.do_audit()

        # There was one page in this session
        self.assertEqual(1, len(report))
        result = report[0]

        # It is expected that no rules will be ignored because we have set
        # rules_to_ignore to [] (which translates to 'ingore none'),
        # and rules_to_run to [] (which means 'run all').
        self.assertEqual(2, len(result.errors))
        self.assertIn(self.ax_aria_01_errors, result.errors)
        self.assertIn(self.ax_aria_04_errors, result.errors)
        self.assertEqual(1, len(result.warnings))

    def test_check_for_accessibility_errors(self):
        page = AccessibilityPage(self.browser)
        page.visit()
        with self.assertRaises(AccessibilityError):
            page.a11y_audit.check_for_accessibility_errors()

    def test_no_results_returned(self):
        page = AccessibilityPage(self.browser)
        page.visit()
        mock_response = Response()
        mock_response.json = Mock(return_value={"value": None})

        with patch('requests.post', return_value=mock_response):
            with self.assertRaises(RuntimeError):
                page.a11y_audit.do_audit()


@patch.dict(os.environ, {'BOKCHOY_A11Y_RULESET': 'axe_core'})
class AxeCoreAccessibilityTest(WebAppTest):
    """
    Test axe-core ruleset accessibility audit integration.
    """
    @patch.dict(os.environ, {'SELENIUM_BROWSER': 'phantomjs'})
    def setUp(self):
        super(AxeCoreAccessibilityTest, self).setUp()
        self.page = AccessibilityPage(self.browser)

    def _do_audit_and_check_errors(self, expected_errors):
        self.page.visit()
        report = self.page.a11y_audit.do_audit()
        self.assertEqual(1, len(report))
        errors = self.page.a11y_audit.get_errors(report)
        self.assertEqual(expected_errors, errors["total"])

    def test_missing_rules_file(self):
        self.page.a11y_audit.config.set_rules_file("nonexistent_file")
        self.page.visit()
        with self.assertRaises(RuntimeError):
            report = self.page.a11y_audit.do_audit()

    def test_default_config(self):
        self._do_audit_and_check_errors(6)

    def test_ignored_rule(self):
        self.page.a11y_audit.config.set_rules(['aria-roles'], ignore=True)
        self._do_audit_and_check_errors(4)

    def test_limited_rules(self):
        self.page.a11y_audit.config.set_rules(['aria-roles'])
        self._do_audit_and_check_errors(2)

    def test_limited_rule_tags(self):
        self.page.a11y_audit.config.set_rules(['wcag111'], include_type="tag")
        self._do_audit_and_check_errors(1)

    def test_exclude_scope(self):
        self.page.a11y_audit.config.set_scope(exclude=['#bad-link'])
        self._do_audit_and_check_errors(5)

    def test_include_scope(self):
        self.page.a11y_audit.config.set_scope(include=['#limit_scope'])
        self._do_audit_and_check_errors(1)

    def test_include_and_exclude_scope(self):
        self.page.a11y_audit.config.set_scope(
            exclude=['#limit_scope'],
            include=['#bad-link']
        )
        self._do_audit_and_check_errors(1)

    def test_set_rules_and_scope(self):
        self.page.a11y_audit.config.set_scope(
            exclude=['#limit_scope'],
            include=['#bad-link']
        )
        self._do_audit_and_check_errors(1)

    def test_check_for_accessibility_errors(self):
        self.page.visit()
        with self.assertRaises(AccessibilityError):
            self.page.a11y_audit.check_for_accessibility_errors()

    def test_no_results_returned(self):
        self.page.visit()
        mock_response = Response()
        mock_response.json = Mock(return_value={"value": None})

        with patch('requests.post', return_value=mock_response):
            with self.assertRaises(BrokenPromise):
                self.page.a11y_audit.do_audit()


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
