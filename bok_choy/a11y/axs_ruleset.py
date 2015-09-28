"""
Interface for using the google accessibility ruleset.
See: https://github.com/GoogleChrome/accessibility-developer-tools
"""
import json
import logging
import os
import requests

from collections import namedtuple
from textwrap import dedent

from .a11y_audit import A11yAudit, A11yAuditConfig, AccessibilityError

log = logging.getLogger(__name__)
AuditResults = namedtuple('AuditResults', 'errors, warnings')
CUR_DIR = os.path.dirname(os.path.abspath(__file__))


class AxsAuditConfig(A11yAuditConfig):
    """
    The `AxsAuditConfig` object defines the options available when
    running an `AxsAudit`.
    """
    def __init__(self, *args, **kwargs):
        super(AxsAuditConfig, self).__init__(*args, **kwargs)
        self.rules_file = None
        self.scope, self.rules_to_run, self.rules_to_ignore = None, None, None
        self.rules_file = os.path.join(
            os.path.split(CUR_DIR)[0],
            'vendor/google/axs_testing.js'
        )
        self.set_rules({})
        self.set_scope()

    def set_rules(self, rules):
        """
        Sets the rules to be run or ignored for the audit.

        Args:

            rules: a dictionary of the format `{"ignore": [], "apply": []}`.

        See https://github.com/GoogleChrome/accessibility-developer-tools/tree/master/src/audits

        Passing `{"apply": []}` or `{}` means to check for all available rules.

        Passing `{"apply": None}` means that no audit should be done for this page.

        Passing `{"ignore": []}` means to run all otherwise enabled rules.
        Any rules in the "ignore" list will be ignored even if they were also
        specified in the "apply".

        Examples:

            To check only `badAriaAttributeValue`::

                page.a11y_audit.config.set_rules({
                    "apply": ['badAriaAttributeValue']
                })

            To check all rules except `badAriaAttributeValue`::

                page.a11y_audit.config.set_rules(
                    "ignore": ['badAriaAttributeValue'],
                )
        """
        self.rules_to_ignore = rules.get("ignore", [])
        self.rules_to_run = rules.get("apply", [])

    def set_scope(self, include=None, exclude=None):
        """
        Sets `scope`, the "start point" for the audit.

        Args:

            include: A list of css selectors specifying the elements that
                contain the portion of the page that should be audited.
                Defaults to auditing the entire document.
            exclude: This arg is not implemented in this ruleset.

        Examples:

            To check only the `div` with id `foo`::

                page.a11y_audit.config.set_scope(["div#foo"])

            To reset the scope to check the whole document::

                page.a11y_audit.config.set_scope()
        """
        if include:
            self.scope = "document.querySelector(\"{}\")".format(
                ', '.join(include)
            )
        else:
            self.scope = "null"

        if exclude is not None:
            raise NotImplementedError(
                "The argument `exclude` has not been implemented in "
                "AxsAuditConfig.set_scope method."
            )


class AxsAudit(A11yAudit):
    """
    Use Google's Accessibility Developer Tools to audit a
    page for accessibility problems.

    See https://github.com/GoogleChrome/accessibility-developer-tools

    Since this needs to inject JavaScript into the browser page, the only
    known way to do this is to use PhantomJS as your browser.
    """

    @property
    def default_config(self):
        """
        Returns an instance of a subclass of AxsAuditConfig.
        """
        return AxsAuditConfig()

    @staticmethod
    def _check_rules(ghostdriver_url, session_id, config):
        """
        Check the page for violations of the configured rules. By default,
        all rules in the ruleset will be checked.

        Args:
            ghostdriver_url: url of ghostdriver.
            session_id: a session id to test.
            config: an AxsAuditConfig instance.

        Returns:
            A namedtuple with 'errors' and 'warnings' fields whose values are
            the errors and warnings returned from the audit.

            None if config has rules_to_run set to None.

        __Caution__: You probably don't really want to call this method
        directly! It will be used by `A11yAudit.do_audit` if using this ruleset.
        """
        if config.rules_to_run is None:
            msg = 'No accessibility rules were specified to check.'
            log.warning(msg)
            return None

        # This line will only be included in the script if rules to check on
        # this page are specified, as the default behavior of the js is to
        # run all rules.
        rules = config.rules_to_run
        if len(rules) > 0:
            rules_config = "auditConfig.auditRulesToRun = {rules};".format(
                rules=rules)
        else:
            rules_config = ""

        ignored_rules = config.rules_to_ignore
        if ignored_rules:
            rules_config += (
                "\nauditConfig.auditRulesToIgnore = {rules};".format(
                    rules=ignored_rules
                )
            )

        script = dedent("""
            return this.evaluate(function() {{
              var auditConfig = new axs.AuditConfiguration();
              {rules_config}
              auditConfig.scope = {scope};
              var run_results = axs.Audit.run(auditConfig);
              var audit_results = axs.Audit.auditResults(run_results)
              return audit_results;
            }});
        """.format(rules_config=rules_config, scope=config.scope))

        payload = {"script": script, "args": []}
        resp = requests.post('{}/session/{}/phantom/execute'.format(
            ghostdriver_url, session_id), data=json.dumps(payload))

        result = resp.json().get('value')
        if result is None:
            msg = '{} {} \nScript:{} \nResponse:{}'.format(
                'No results were returned by the audit report.',
                (
                    'Perhaps there was a problem with the rules or scope '
                    'defined for this page.'
                ),
                script,
                resp.text)
            raise RuntimeError(msg)

        # audit_results is report of accessibility errors for that session
        audit_results = AuditResults(
            errors=result.get('errors_'),
            warnings=result.get('warnings_')
        )
        return audit_results

    @staticmethod
    def get_errors(audit):
        """
        Args:

            audit: results of `AxsAudit.do_audit()`.

        Returns: a list of errors.
        """
        errors = []
        for session_result in audit:
            if session_result:
                if session_result.errors:
                    errors.extend(session_result.errors)

        return errors

    @staticmethod
    def report_errors(audit, url):
        """
        Args:

            audit: results of `AxsAudit.do_audit()`.
            url: the url of the page being audited.

        Raises: `AccessibilityError`
        """
        errors = AxsAudit.get_errors(audit)
        if errors:
            msg = "URL '{}' has {} errors:\n{}".format(
                url,
                len(errors),
                (', ').join(errors)
            )
            raise AccessibilityError(msg)
