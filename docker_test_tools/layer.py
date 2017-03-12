"""
Define a nose2 test layer for managing the tests environment.

For more info about test layers: https://nose2.readthedocs.io/en/latest/plugins/layers.html
"""


def get_layer(controller):

    class EnvironmentLayer(object):
        """Manage the subsystem tests environment using nose2 layer mechanism."""
        CONTROLLER = controller

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

    return EnvironmentLayer


