import unittest
from six import PY3

if PY3:
    from unittest.mock import MagicMock, patch
else:
    from mock import MagicMock, patch

from docker_test_tools.compose import Compose


class TestCompose(unittest.TestCase):
    def setUp(self):
        self.compose = Compose("path", "project", "env", "command")

    @patch("subprocess.check_output")
    def test_get_services(self, mock_check_output):
        mock_check_output.return_value = "service1\nservice2\n"
        services = self.compose.get_services()
        self.assertEqual(services, ["service1", "service2"])
        mock_check_output.assert_called_once()

    @patch("subprocess.check_output")
    def test_up(self, mock_check_output):
        mock_check_output.return_value = ""
        self.compose.up()
        mock_check_output.assert_called_once()

    @patch("subprocess.check_output")
    def test_down(self, mock_check_output):
        mock_check_output.return_value = ""
        self.compose.down()
        mock_check_output.assert_called_once()

    @patch("subprocess.check_output")
    def test_get_service_container_id(self, mock_check_output):
        mock_check_output.return_value = "container_id"
        container_id = self.compose.get_service_container_id("service_name")
        self.assertEqual(container_id, "container_id")
        mock_check_output.assert_called_once()

    @patch("subprocess.Popen")
    def test_start_logs_collector(self, mock_popen):
        mock_popen.return_value = MagicMock()
        self.compose.start_logs_collector("stdout")
        mock_popen.assert_called_once()

    def test_stop_logs_collector(self):
        with patch.object(self.compose, "logs_process") as mock_popen:
            self.compose.stop_logs_collector()
            mock_popen.kill.assert_called_once()
            mock_popen.wait.assert_called_once()
