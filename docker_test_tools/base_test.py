import os
import unittest

import layer
import utils
import environment


class BaseDockerTest(unittest.TestCase):
    """Basic docker test.

    Manage the required containers setup and tear down.

    When subclassing, you can set these attributes:

    * CHECKS_TIMEOUT: Define the timeout (in seconds) for the required services start up.
    * CHECKS_INTERVAL: Define the interval (in seconds) for sampling required services checks.
    * REQUIRED_HEALTH_CHECKS: Define the health checks (callables) to pass up before the test starts running.
    """
    controller = environment.EnvironmentController.from_file(config_path=os.environ.get('CONFIG', None))

    # Define the common methods for the subsystem tests (global setUp and tearDown, and testSetUp).
    layer = layer.get_layer(controller=controller)

    # Override this value to define the timeout (in seconds) for the required checks to pass.
    CHECKS_TIMEOUT = 60

    # Override this value to define the interval (in seconds) for sampling required checks to pass.
    CHECKS_INTERVAL = 1

    # Override this value to define the health checks (callables) to pass up before the test starts running.
    REQUIRED_HEALTH_CHECKS = []

    def setUp(self):
        # Wait for docker inspection on the services to pass
        self.assertTrue(self.controller.wait_for_services(interval=self.CHECKS_INTERVAL, timeout=self.CHECKS_TIMEOUT),
                        "Required checks didn't pass within timeout")

        if self.REQUIRED_HEALTH_CHECKS:
            # Wait for user defined health checks to pass
            self.assertTrue(
                utils.run_health_checks(checks=self.REQUIRED_HEALTH_CHECKS,
                                        timeout=self.CHECKS_TIMEOUT,
                                        interval=self.CHECKS_INTERVAL),
                "Required health checks didn't pass within timeout"
            )
