"""
Specify test fixtures.  In this context, a "fixture" is a
pre-condition for running a test.

Examples:

    * A user exists with a particular username and password.
    * A file has been uploaded with a particular name.
"""

from abc import ABCMeta, abstractproperty, abstractmethod
from fabric.api import execute, env, hide
from fabric.network import disconnect_all


class WebAppFixtureError(Exception):
    """
    An error occurred while installing a test fixture.
    """
    pass


class WebAppFixture(object):
    """
    Define a "fixture" (pre-condition) for running a test.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def install(self):
        """
        Guarantee that the fixture conditions are satisfied.
        Examples:

            * Create a user with a particular name if the user does not already exist.
            * Upload a file with a particular name if it does not already exist.

        This operation needs to satisfy these conditions:

            1) Synchronous: When execution completes, the state should be set.
            2) Test-Independent: Should not interfere with the execution
                of any test (including multiple runs of the same test)

        Counter-examples:
            * Clearing the database (may interfere with other tests)
            * Changing a configuration setting (may interfere with other tests)
            * Starting an import, but returning before it finishes (not synchronous)

        One technique for ensuring test independence is to use
        `WebAppTest.unique_id`.  For example, you might include
        the unique id in the username to ensure each test
        creates a unique user, thereby avoiding collisions between tests.

        Another technique is to ensure that install operations are idempotent.
        For example, if the fixture is "ensure this file is uploaded",
        then upload the file only if it does not already exist.

        Concrete subclasses implement the operation using whatever mechanism
        necessary (ssh commands, REST HTTP requests, Django admin commands,
        database queries, etc.).
        """
        pass


class RemoteCommandFixture(WebAppFixture):
    """
    A fixture created by executing ssh commands on the remote host.
    """

    __metaclass__ = ABCMeta

    def __init__(self, hostname, ssh_user=None, ssh_keyfile=None):
        """
        Configure the fixture to execute on `hostname`.

        `ssh_user` is the account to log in with via ssh
        `ssh_keyfile` is the full path to the private ssh key
        """
        self.hostname = hostname
        self.ssh_user = ssh_user
        self.ssh_keyfile = ssh_keyfile

    def install(self):
        """
        Execute ssh commands on the remote host.
        """
        try:
            env.key_filename = self.ssh_keyfile

            if self.ssh_user is not None:
                host = "{0}@{1}".format(self.ssh_user, self.hostname)
            else:
                host = self.hostname

            with hide('output', 'running'):
                execute(self.execute, hosts=[host])

        finally:
            with hide('output', 'running'):
                disconnect_all()

    @abstractmethod
    def execute(self):
        """
        Execute commands on the remote host using Fabric.
        """
        pass

    def cmd(self, *args):
        """
        Helper method to construct a command string from component args.
        """
        return u" ".join([u"{0}".format(val) for val in args])
