import mock
import unittest

from docker_test_tools.layer import EnvironmentLayer


class TestLayer(unittest.TestCase):

    @mock.patch('docker_test_tools.environment.EnvironmentController.setup')
    def test_layer_setup(self, setup_mock):
        """Validate the layer setUp method."""
        EnvironmentLayer.setUp()
        setup_mock.assert_called_once_with()

    @mock.patch('docker_test_tools.environment.EnvironmentController.teardown')
    def test_layer_teardown(self, teardown_mock):
        """Validate the layer tearDown method."""
        EnvironmentLayer.tearDown()
        teardown_mock.assert_called_once_with()
