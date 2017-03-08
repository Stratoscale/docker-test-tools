import unittest

import layer
import utils


class BaseDockerTest(unittest.TestCase):
    """Basic docker test.

    Manage the required containers setup and tear down.

    When subclassing, you can set these attributes:

    * REQUIRED_HEALTH_CHECKS: Define the required services health checks to pass up before the test starts running.
    * HEALTH_CHECKS_TIMEOUT: Define the timeout (in seconds) for the required services start up.
    * HEALTH_CHECKS_INTERVAL: Define the interval (in seconds) for sampling required services health checks.

    """
    # Define the common methods for the subsystem tests (global setUp and tearDown, and testSetUp).
    layer = layer.EnvironmentLayer

    # Override this value to define the health checks (callables) to pass up before the test starts running.
    REQUIRED_HEALTH_CHECKS = []

    # Override this value to define the timeout (in seconds) for the required health checks to pass.
    HEALTH_CHECKS_TIMEOUT = 60

    # Override this value to define the interval (in seconds) for sampling required health checks to pass.
    HEALTH_CHECKS_INTERVAL = 1

    def setUp(self):
        self.assertTrue(
            utils.run_health_checks(checks=self.REQUIRED_HEALTH_CHECKS,
                                    timeout=self.HEALTH_CHECKS_TIMEOUT,
                                    interval=self.HEALTH_CHECKS_INTERVAL),
            "Required health checks didn't pass within timeout"
        )
