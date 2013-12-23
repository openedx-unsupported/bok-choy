"""
Specify test fixtures.  In this context, a "fixture" is a
pre-condition for running a test.

Examples:

    * A user exists with a particular username and password.
    * A file has been uploaded with a particular name.
"""

from abc import ABCMeta, abstractmethod


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
