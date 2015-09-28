"""
Interface for using the axe-core ruleset.
See: https://github.com/dequelabs/axe-core
"""
import json
import os
import requests

from textwrap import dedent, fill

from .a11y_audit import A11yAudit, A11yAuditConfig, AccessibilityError
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
        self.rules_file = os.path.join(
            os.path.split(CUR_DIR)[0],
            'vendor/axe-core/axe.min.js'
        )
        self.set_rules({})
        self.set_scope()

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


class AxeCoreAudit(A11yAudit):
    """
    Use Deque Labs' axe-core engine to audit a page for accessibility issues.

    Since this needs to inject JavaScript into the browser page, the only
    known way to do this is to use PhantomJS as your browser.

    Related documentation:

        https://github.com/dequelabs/axe-core/blob/master/doc/API.md
    """

    @property
    def default_config(self):
        """
        Returns an instance of a subclass of AxeCoreAuditConfig.
        """
        return AxeCoreAuditConfig()

    @staticmethod
    def _check_rules(ghostdriver_url, session_id, config):
        """
        Run an accessibility audit on the page using the axe-core ruleset.

        Args:
            ghostdriver_url: url of ghostdriver.
            session_id: a session id to test.
            config: an AxsAuditConfig instance.

        Returns:
            A list of violations.

        Related documentation:

            https://github.com/dequelabs/axe-core/blob/master/doc/API.md#results-object

        __Caution__: You probably don't really want to call this method
        directly! It will be used by `AxeCoreAudit.do_audit`.
        """
        script_url = '{}/session/{}/phantom/execute'.format(
            ghostdriver_url, session_id)

        audit_run_script = dedent("""
            return this.evaluate(function(){{
                var updatedResults = function(r) {{
                    window.a11yAuditResults = JSON.stringify(r);
                    window.console.log(window.a11yAuditResults);
                }}

                axe.a11yCheck({context}, {options}, updatedResults);
            }});
        """.format(context=config.context, options=config.rules))

        audit_results_script = dedent("""
            return this.evaluate(function(){{
                window.console.log(window.a11yAuditResults);
                return window.a11yAuditResults;
            }});
        """)

        requests.post(
            script_url,
            data=json.dumps({"script": audit_run_script, "args": []}),
        )

        def audit_results_check_func():
            """
            A method to check that the audit has completed.

            Returns:

                (True, results) if the results are available.
                (False, None) if the results aren't available.
            """
            resp = requests.post(
                script_url,
                data=json.dumps({"script": audit_results_script, "args": []})
            )

            try:
                results = json.loads(resp.json().get('value'))
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
    def get_errors(audit):
        """
        Args:

            audit: results of `AxeCoreAudit.do_audit()`.

        Returns:

            A dictionary with keys "errors" and "total".
        """
        errors = {"errors": [], "total": 0}
        for session_result in audit:
            if session_result:
                errors["errors"].extend(session_result)
                for i in session_result:
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
        lines = []
        for error_type in errors:
            lines.append("Rule ID: {}".format(error_type.get("id")))
            lines.append("Help URL: {}\n".format(error_type.get('helpUrl')))

            for node in error_type['nodes']:
                try:
                    msg = node['message']
                except KeyError:
                    try:
                        msg = node['any'][0]['message']
                    except (KeyError, IndexError):
                        msg = ''

                msg = "Message: {}".format(msg)
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
