import os
import unittest

import layer
import config
import environment


class BaseDockerTest(unittest.TestCase):
    """Basic docker test.

    Manage the required containers setup and tear down.

    When subclassing, you can set these attributes:

    * CHECKS_TIMEOUT: Define the timeout (in seconds) for the required services start up.
    * CHECKS_INTERVAL: Define the interval (in seconds) for sampling required services checks.

    """
    config = config.Config(config_path=os.environ.get('CONFIG', None))
    controller = environment.EnvironmentController(log_path=config.log_path,
                                                   project_name=config.project_name,
                                                   compose_path=config.docker_compose_path,
                                                   reuse_containers=config.reuse_containers)

    # Define the common methods for the subsystem tests (global setUp and tearDown, and testSetUp).
    layer = layer.get_layer(controller=controller)

    # Override this value to define the timeout (in seconds) for the required checks to pass.
    CHECKS_TIMEOUT = 60

    # Override this value to define the interval (in seconds) for sampling required checks to pass.
    CHECKS_INTERVAL = 1

    def setUp(self):
        self.assertTrue(self.controller.wait_for_services(interval=self.CHECKS_INTERVAL, timeout=self.CHECKS_TIMEOUT),
                        "Required checks didn't pass within timeout")
