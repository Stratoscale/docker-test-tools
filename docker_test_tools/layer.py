"""
Define a nose2 test layer for managing the tests environment.

For more info about test layers: https://nose2.readthedocs.io/en/latest/plugins/layers.html
"""
import os

import config
import environment


class EnvironmentLayer(object):
    """Manage the subsystem tests environment using nose2 layer mechanism."""
    CONFIG = config.Config(config_path=os.environ.get('CONFIG', None))
    CONTROLLER = environment.EnvironmentController(log_path=CONFIG.log_path,
                                                   project_name=CONFIG.project_name,
                                                   compose_path=CONFIG.docker_compose_path,
                                                   reuse_containers=CONFIG.reuse_containers)

    @classmethod
    def setUp(cls):
        """Sets up the subsystem environment using docker commands.

        Called once before *all* the tests start.
        """
        cls.CONTROLLER.setup()

    @classmethod
    def tearDown(cls):
        """Tears down the subsystem environment using docker commands.

        Called once after *all* the tests finish.
        """
        cls.CONTROLLER.teardown()
