"""
Interface for using the axe-core ruleset.
See: https://github.com/dequelabs/axe-core
"""
from __future__ import absolute_import

import json
import os

from textwrap import dedent, fill

from .a11y_audit import A11yAudit, A11yAuditConfig, AccessibilityError, A11yAuditConfigError
from ..promise import Promise


CUR_DIR = os.path.dirname(os.path.abspath(__file__))


class AxeCoreAuditConfig(A11yAuditConfig):
    """
    The `AxeCoreAuditConfig` object defines the options available when
    running an `AxeCoreAudit`.
    """
    def __init__(self, *args, **kwargs):
        super(AxeCoreAuditConfig, self).__init__(*args, **kwargs)
        self.rules, self.context = None, None
        self.custom_rules = "customRules={}"
        self.rules_file = os.path.join(
            os.path.split(CUR_DIR)[0],
            'vendor/axe-core/axe.min.js'
        )

        self.set_rules({})
        self.set_scope()
        self.customize_ruleset()

    def set_rules(self, rules):
        """
        Set rules to ignore XOR limit to when checking for accessibility
        errors on the page.

        Args:

            rules: a dictionary one of the following formats.
                If you want to run all of the rules except for some::

                    {"ignore": []}

                If you want to run only a specific set of rules::

                    {"apply": []}

                If you want to run only rules of a specific standard::

                    {"tags": []}

        Examples:

            To run only "bad-link" and "color-contrast" rules::

                page.a11y_audit.config.set_rules({
                    "apply": ["bad-link", "color-contrast"],
                })

            To run all rules except for "bad-link" and "color-contrast"::

                page.a11y_audit.config.set_rules({
                    "ignore": ["bad-link", "color-contrast"],
                })

            To run only WCAG 2.0 Level A rules::

                page.a11y_audit.config.set_rules({
                    "tags": ["wcag2a"],
                })

            To run all rules:
                page.a11y_audit.config.set_rules({})

        Related documentation:

            * https://github.com/dequelabs/axe-core/blob/master/doc/API.md#options-parameter-examples
            * https://github.com/dequelabs/axe-core/doc/rule-descriptions.md
        """
        options = {}
        if rules:
            if rules.get("ignore"):
                options["rules"] = {}
                for rule in rules.get("ignore"):
                    options["rules"][rule] = {"enabled": False}
            elif rules.get("apply"):
                options["runOnly"] = {
                    "type": "rule",
                    "values": rules.get("apply"),
                }
            elif rules.get("tags"):
                options["runOnly"] = {
                    "type": "tag",
                    "values": rules.get("tags"),
                }
        self.rules = json.dumps(options)

    def set_scope(self, include=None, exclude=None):
        """
        Sets `scope` (refered to as `context` in ruleset documentation), which
        defines the elements on a page to include or exclude in the audit. If
        neither `include` nor `exclude` are passed, the entire document will
        be included.

        Args:

            include (optional): a list of css selectors for elements that
            should be included in the audit. By, default, the entire document
            is included.
            exclude (optional): a list of css selectors for elements that should not
            be included in the audit.

        Examples:

            To include all items in `#main-content` except `#some-special-elm`::

                page.a11y_audit.config.set_scope(
                    exclude=["#some-special-elm"],
                    include=["#main-content"]
                )

            To include all items in the document except `#some-special-elm`::

                page.a11y_audit.config.set_scope(
                    exclude=["#some-special-elm"],
                )

            To include only children of `#some-special-elm`::

                page.a11y_audit.config.set_scope(
                    include=["#some-special-elm"],
                )

        Context documentation:

            https://github.com/dequelabs/axe-core/blob/master/doc/API.md#a-context-parameter

            Note that this implementation only supports css selectors. It does
            not accept nodes as described in the above documentation resource.
        """
        context = {}

        if exclude:
            context["exclude"] = [[selector] for selector in exclude]

        if include:
            context["include"] = [[selector] for selector in include]

        self.context = json.dumps(context) if context else 'document'

    def customize_ruleset(self, custom_ruleset_file=None):
        """
        Updates the ruleset to include a set of custom rules. These rules will
        be _added_ to the existing ruleset or replace the existing rule with
        the same ID.

        Args:

            custom_ruleset_file (optional): The filepath to the custom rules.
                Defaults to `None`. If `custom_ruleset_file` isn't passed, the
                environment variable `BOKCHOY_A11Y_CUSTOM_RULES_FILE` will be
                checked. If a filepath isn't specified by either of these
                methods, the ruleset will not be updated.

        Raises:

            `IOError` if the specified file does not exist.

        Examples:

            To include the rules defined in `axe-core-custom-rules.js`::

                page.a11y_audit.config.customize_ruleset(
                    "axe-core-custom-rules.js"
                )

            Alternatively, use the environment variable `BOKCHOY_A11Y_CUSTOM_RULES_FILE`
            to specify the path to the file containing the custom rules.

        Documentation for how to write rules:

            https://github.com/dequelabs/axe-core/blob/master/doc/developer-guide.md

        An example of a custom rules file can be found at
        https://github.com/edx/bok-choy/tree/master/tests/a11y_custom_rules.js
        """
        custom_file = custom_ruleset_file or os.environ.get(
            "BOKCHOY_A11Y_CUSTOM_RULES_FILE"
        )

        if not custom_file:
            return

        with open(custom_file, "r") as additional_rules:
            custom_rules = additional_rules.read()

        if "var customRules" not in custom_rules:
            raise A11yAuditConfigError(
                "Custom rules file must include \"var customRules\""
            )

        self.custom_rules = custom_rules


class AxeCoreAudit(A11yAudit):
    """
    Use Deque Labs' axe-core engine to audit a page for accessibility issues.

    Related documentation:

        https://github.com/dequelabs/axe-core/blob/master/doc/API.md
    """

    @property
    def default_config(self):
        """
        Returns an instance of AxeCoreAuditConfig.
        """
        return AxeCoreAuditConfig()

    @staticmethod
    def _check_rules(browser, rules_js, config):
        """
        Run an accessibility audit on the page using the axe-core ruleset.

        Args:
            browser: a browser instance.
            rules_js: the ruleset JavaScript as a string.
            config: an AxsAuditConfig instance.

        Returns:
            A list of violations.

        Related documentation:

            https://github.com/dequelabs/axe-core/blob/master/doc/API.md#results-object

        __Caution__: You probably don't really want to call this method
        directly! It will be used by `AxeCoreAudit.do_audit`.
        """
        audit_run_script = dedent("""
            {rules_js}
            {custom_rules}
            axe.configure(customRules);
            var updatedResults = function(r) {{
                window.a11yAuditResults = JSON.stringify(r);
                window.console.log(window.a11yAuditResults);
            }}
            axe.a11yCheck({context}, {options}, updatedResults);
        """).format(
            rules_js=rules_js,
            custom_rules=config.custom_rules,
            context=config.context,
            options=config.rules
        )

        audit_results_script = dedent("""
            window.console.log(window.a11yAuditResults);
            return window.a11yAuditResults;
        """)

        browser.execute_script(audit_run_script)

        def audit_results_check_func():
            """
            A method to check that the audit has completed.

            Returns:

                (True, results) if the results are available.
                (False, None) if the results aren't available.
            """

            unicode_results = browser.execute_script(audit_results_script)

            try:
                results = json.loads(unicode_results)
            except (TypeError, ValueError):
                results = None

            if results:
                return True, results
            else:
                return False, None

        result = Promise(
            audit_results_check_func,
            "Timed out waiting for a11y audit results.",
            timeout=5,
        ).fulfill()

        # audit_results is report of accessibility violations for that session
        # Note that this ruleset doesn't have distinct error/warning levels.
        audit_results = result.get('violations')
        return audit_results

    @staticmethod
    def get_errors(audit_results):
        """
        Args:

            audit_results: results of `AxeCoreAudit.do_audit()`.

        Returns:

            A dictionary with keys "errors" and "total".
        """
        errors = {"errors": [], "total": 0}
        if audit_results:
            errors["errors"].extend(audit_results)
            for i in audit_results:
                for _node in i["nodes"]:
                    errors["total"] += 1
        return errors

    @staticmethod
    def format_errors(errors):
        """
        Args:

            errors: results of `AxeCoreAudit.get_errors()`.

        Returns: The errors as a formatted string.
        """

        def _get_message(node):
            """
            Get the message to display in the error output.
            """
            messages = set()

            try:
                messages.update([node['message']])
            except KeyError:
                pass

            for check_group in ['any', 'all', 'none']:
                try:
                    for check in node[check_group]:
                        messages.update([check.get('message')])
                except KeyError:
                    pass

            messages = messages.difference([''])
            return '; '.join(messages)

        lines = []
        for error_type in errors:
            lines.append("Severity: {}".format(error_type.get("impact")))
            lines.append("Rule ID: {}".format(error_type.get("id")))
            lines.append("Help URL: {}\n".format(error_type.get('helpUrl')))

            for node in error_type['nodes']:
                msg = "Message: {}".format(_get_message(node))
                html = "Html: {}".format(node.get('html').encode('utf-8'))
                target = "Target: {}".format(node.get('target'))
                fill_opts = {
                    'width': 100,
                    'initial_indent': '\t',
                    'subsequent_indent': '\t\t',
                }
                lines.append(fill(msg, **fill_opts))
                lines.append(fill(html, **fill_opts))
                lines.append(fill(target, **fill_opts))
                lines.append('\n')

        return '\n'.join(lines)

    @staticmethod
    def report_errors(audit, url):
        """
        Args:

            audit: results of `AxeCoreAudit.do_audit()`.
            url: the url of the page being audited.

        Raises: `AccessibilityError`
        """
        errors = AxeCoreAudit.get_errors(audit)
        if errors["total"] > 0:
            msg = "URL '{}' has {} errors:\n\n{}".format(
                url,
                errors["total"],
                AxeCoreAudit.format_errors(errors["errors"])
            )
            raise AccessibilityError(msg)
