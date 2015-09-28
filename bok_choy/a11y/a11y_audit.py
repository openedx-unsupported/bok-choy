"""
Interface for running accessibility audits on a PageObject.
"""
import json
import os
import requests

from abc import abstractmethod, abstractproperty, ABCMeta
from textwrap import dedent


class AccessibilityError(Exception):
    """
    The page violates one or more accessibility rules.
    """
    pass


class A11yAuditConfig(object):
    """
    The `A11yAuditConfig` object defines the options available in an
    accessibility ruleset.
    """
    __metaclass__ = ABCMeta

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
    __metaclass__ = ABCMeta

    def __init__(self, browser, url, config=None, *args, **kwargs):
        """
        Sets ruleset to be used.

        Args:
            browser: A phantomjs browser instance
            url: URL of the page to test
            config: (optional) A11yAuditConfig or subclass of A11yAuditConfig
        """
        super(A11yAudit, self).__init__(*args, **kwargs)
        self.url = url
        self.browser = browser
        self.config = config or self.default_config

    def _phantomjs_setup(self):
        """
        Verifies that phantomjs is being used and returns the ghostdriver URL
        and session information.

        Returns: (ghostdriver_url, sessions) where sessions is a list of
            session ids.

        Raises: `NotImplementedError` if not using phantomjs.
        """
        if self.browser.name != 'phantomjs':
            msg = (
                'Accessibility auditing is only supported with PhantomJS as'
                ' the browser.'
            )
            raise NotImplementedError(msg)

        # The ghostdriver URL will be something like this:
        # 'http://localhost:33225/wd/hub'
        ghostdriver_url = self.browser.service.service_url

        # Get the session_id from ghostdriver so that we can inject JS into
        # the page.
        resp = requests.get('{}/sessions'.format(ghostdriver_url))
        sessions = resp.json()

        return ghostdriver_url, sessions

    def _verify_rules_file_exists(self):
        """
        Checks that the rules file for the enabled ruleset exists.

        Raises: `RuntimeError` if the file isn't found.
        """
        if not os.path.isfile(self.config.rules_file):
            msg = 'Could not find the accessibility tools JS file: {}'.format(
                self.config.rules_file)
            raise RuntimeError(msg)

    def do_audit(self):
        """
        Audit the page for accessibility problems using the enabled ruleset.

        Since this needs to inject JavaScript into the browser page, the only
        known way to do this is to use PhantomJS as your browser.

        Raises:

            * NotImplementedError if you are not using PhantomJS
            * RuntimeError if there was a problem with the injected JS or
                getting the report

        Returns:
            A list (one for each browser session) of results returned from
            the audit. See documentation of `_check_rules` in the enabled
            ruleset for the format of each result.
            `None` if no results are returned.
        """
        ghostdriver_url, sessions = self._phantomjs_setup()
        self._verify_rules_file_exists()

        # report is the list that is returned, with one item for each
        # browser session.
        report = []
        for session in sessions.get('value'):
            session_id = session.get('id')

            # First make sure you can successfully inject the JS on the page
            script = dedent("""
                return this.injectJs("{file}");
            """.format(file=self.config.rules_file))

            payload = {"script": script, "args": []}
            resp = requests.post('{}/session/{}/phantom/execute'.format(
                ghostdriver_url, session_id), data=json.dumps(payload))

            result = resp.json().get('value')

            if result is False:
                msg = '{msg} \nScript:{script} \nResponse:{response}'.format(
                    msg=(
                        'Failure injecting the Accessibility Audit JS '
                        'on the page.'
                    ),
                    script=script,
                    response=resp.text)
                raise RuntimeError(msg)

            audit_results = self._check_rules(
                ghostdriver_url, session_id, self.config)

            if audit_results:
                report.append(audit_results)

        return report or None

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
    def _check_rules(ghostdriver_url, session_id, config):
        """
        Run an accessibility audit on the page using the implemented ruleset.

        Args:

            ghostdriver_url: url of ghostdriver.
            session_id: a session id to test.
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
