"""
Interface for running accessibility audits on a PageObject.
"""
from __future__ import absolute_import

import os
from abc import abstractmethod, abstractproperty, ABCMeta
import six


class AccessibilityError(Exception):
    """
    The page violates one or more accessibility rules.
    """
    pass


class A11yAuditConfigError(Exception):
    """
    An error in A11yAuditConfig.
    """
    pass


@six.add_metaclass(ABCMeta)
class A11yAuditConfig(object):
    """
    The `A11yAuditConfig` object defines the options available in an
    accessibility ruleset.
    """

    def __init__(self, *args, **kwargs):
        super(A11yAuditConfig, self).__init__(*args, **kwargs)
        self.rules_file = None

    def set_rules_file(self, path=None):
        """
        Sets `self.rules_file` to the passed file.

        Args:
            A filepath where the JavaScript for the ruleset can be found.

        This is intended to be used in the case of using an extended or
        modified version of the ruleset. The interface and response
        format are expected to be unmodified.
        """
        if path:
            self.rules_file = os.path.abspath(path)

    @abstractmethod
    def set_rules(self, rules):
        """
        Overrides the default rules to be run.

        Raises:

            `NotImplementedError` if this isn't overwritten in the ruleset
                specific implementation.
        """
        raise NotImplementedError(
            "The ability to specify rules has not been implemented."
        )

    @abstractmethod
    def set_scope(self, include=None, exclude=None):
        """
        Overrides the default scope (part of the DOM) to inspect.

        Raises:

            `NotImplementedError` if this isn't overwritten in the ruleset
                specific implementation.
        """
        raise NotImplementedError(
            "The ability to specify scope has not been implemented."
        )

    @abstractmethod
    def customize_ruleset(self, custom_ruleset_file=None):
        """
        Allows customization of the ruleset. (e.g. adding custom rules,
        extending the implementation of an existing rule.)

        Raises:

            `NotImplementedError` if this isn't overwritten in the ruleset
                specific implementation.
        """
        raise NotImplementedError(
            "The ability to customize the ruleset has not been implemented."
        )


@six.add_metaclass(ABCMeta)
class A11yAudit(object):
    """
    Allows auditing of a page for accessibility issues.

    The ruleset to use can be specified by the environment variable
    `BOKCHOY_A11Y_RULESET`. Currently, there are two ruleset implemented:

    `axe_core`:

        * Ruleset class: AxeCoreAudit
        * Ruleset config: AxeCoreAuditConfig
        * This is default ruleset.

    `google_axs`:

        * Ruleset class: AxsAudit
        * Ruleset config: AxsAuditConfig
    """

    def __init__(self, browser, url, config=None, *args, **kwargs):
        """
        Sets ruleset to be used.

        Args:
            browser: A browser instance
            url: URL of the page to test
            config: (optional) A11yAuditConfig or subclass of A11yAuditConfig
        """
        super(A11yAudit, self).__init__(*args, **kwargs)
        self.url = url
        self.browser = browser
        self.config = config or self.default_config

    def _get_rules_js(self):
        """
        Checks that the rules file for the enabled ruleset exists
        and returns its contents as string.

        Raises: `RuntimeError` if the file isn't found.
        """
        if not os.path.isfile(self.config.rules_file):
            msg = 'Could not find the accessibility tools JS file: {}'.format(
                self.config.rules_file)
            raise RuntimeError(msg)

        else:
            with open(self.config.rules_file, "r") as rules_file:
                return rules_file.read()

    def do_audit(self):
        """
        Audit the page for accessibility problems using the enabled ruleset.

        Returns:
            A list (one for each browser session) of results returned from
            the audit. See documentation of `_check_rules` in the enabled
            ruleset for the format of each result.
        """
        rules_js = self._get_rules_js()
        audit_results = self._check_rules(
            self.browser, rules_js, self.config)
        return audit_results

    def check_for_accessibility_errors(self):
        """
        Run an accessibility audit, parse the results, and raise a single
        exception if there are violations.

        Note that an exception is only raised on errors, not on warnings.

        Returns:

            None

        Raises:

            AccessibilityError
        """
        audit_results = self.do_audit()
        if audit_results:
            self.report_errors(audit_results, self.url)

    @abstractproperty
    def default_config(self):
        """
        Return an instance of a subclass of A11yAuditConfig.
        """
        raise NotImplementedError("default_config has not been implemented")

    @staticmethod
    @abstractmethod
    def _check_rules(browser, rules_js, config):
        """
        Run an accessibility audit on the page using the implemented ruleset.

        Args:

            browser: a browser instance.
            rules_js: the ruleset JavaScript as a string.
            config: an AxsAuditConfig instance.

        Returns:

            A list of violations.

        Raises:

            `NotImplementedError` if this isn't overwritten in the ruleset
                specific implementation.
        """
        raise NotImplementedError("_check_rules has not been implemented")

    @staticmethod
    @abstractmethod
    def report_errors(audit, url):
        """
        Args:

            audit: results of an accessibility audit.
            url: the url of the page being audited.

        Raises:

            `AccessibilityError` if errors are found in the audit.
            `NotImplementedError` if this isn't overwritten in the ruleset
                specific implementation.
        """
        raise NotImplementedError("report_errors has not been implemented")
