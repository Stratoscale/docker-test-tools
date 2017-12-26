import unittest

from docker_test_tools import utils


class BaseDockerTest(unittest.TestCase):
    """Basic docker test.

    Manage the required containers setup and tear down.

    When subclassing, you can set these attributes:

    * CHECKS_TIMEOUT: Define the timeout (in seconds) for the required services start up.
    * CHECKS_INTERVAL: Define the interval (in seconds) for sampling required services checks.
    * REQUIRED_HEALTH_CHECKS: Define the health checks (callables) to pass up before the test starts running.
    * WAIT_FOR_SERVICES: Define whether to wait for services health checks at test setup or not.
    """
    # Override to define the timeout (in seconds) for the required checks to pass.
    CHECKS_TIMEOUT = 120

    # Override to define the interval (in seconds) for sampling required checks to pass.
    CHECKS_INTERVAL = 1

    # Override to define the health checks (callables) to pass up before the test starts running.
    REQUIRED_HEALTH_CHECKS = []

    # Override to disable health checks validation before the test starts running.
    WAIT_FOR_SERVICES = True

    def setUp(self):
        """Manage the required containers setup."""
        if self.WAIT_FOR_SERVICES:
            # Wait for docker inspection on the services to pass
            self.assertTrue(
                self.controller.wait_for_services(interval=self.CHECKS_INTERVAL, timeout=self.CHECKS_TIMEOUT),
                "Required checks didn't pass within timeout")

        if self.REQUIRED_HEALTH_CHECKS:
            # Wait for user defined health checks to pass
            self.assertTrue(
                utils.run_health_checks(checks=self.REQUIRED_HEALTH_CHECKS,
                                        timeout=self.CHECKS_TIMEOUT,
                                        interval=self.CHECKS_INTERVAL),
                "Required health checks didn't pass within timeout"
            )
