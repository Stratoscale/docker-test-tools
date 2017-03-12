import mock
import unittest

from docker_test_tools import layer


class TestLayer(unittest.TestCase):

    def setUp(self):
        self.controller = mock.MagicMock()
        self.layer = layer.get_layer(controller=self.controller)

    def test_layer_setup(self):
        """Validate the layer setUp method."""
        self.layer.setUp()
        self.controller.setup.assert_called_once_with()

    def test_layer_teardown(self):
        """Validate the layer tearDown method."""
        self.layer.tearDown()
        self.controller.teardown.assert_called_once_with()
