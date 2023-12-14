import unittest
from six import PY3

if PY3:
    from unittest import mock
else:
    import mock

from docker_test_tools import logs


class TestLogsCollector(unittest.TestCase):
    """Test for the logs collector package.

    TODO: add test_split_logs.
    """
    TEST_ENCODING = 'test-encoding'
    TEST_LOG_PATH = 'test-log-path'
    TEST_COMPOSE_PATH = 'test-compose-path'
    TEST_PROJECT_NAME = 'test-project-name'
    TEST_ENVIRONMENT_VARIABLES = 'test-environment-variables'

    def setUp(self):
        """Create a log collector instance for the test."""
        self.compose_mock = mock.MagicMock()
        self.log_collector = logs.LogCollector(
            log_path=self.TEST_LOG_PATH,
            encoding=self.TEST_ENCODING,
            compose=self.compose_mock,
        )

    @mock.patch("io.open")
    def test_start(self, mock_open):
        """"Validate the log collector start method."""
        mock_test_file = 'test-log-file'
        mock_open.return_value = mock_test_file

        self.log_collector.start()
        mock_open.assert_called_with(self.TEST_LOG_PATH, 'w', encoding=self.TEST_ENCODING)
        self.compose_mock.start_logs_collector.assert_called_with(mock_test_file)
        self.assertEqual(self.log_collector.logs_file, mock_test_file)

    @mock.patch('docker_test_tools.logs.LogCollector._split_logs')
    def test_stop(self, mock_split_logs):
        """"Validate the log collector stop method."""
        self.log_collector.logs_file = mock.MagicMock(name='logs-file-mock')
        self.log_collector.stop()

        self.compose_mock.stop_logs_collector.assert_called_once_with()
        self.log_collector.logs_file.close.assert_called_once_with()
        mock_split_logs.assert_called_once_with()

    def test_write(self):
        """"Validate the log collector write method."""
        test_message = 'test-message'
        self.log_collector.logs_file = mock.MagicMock(name='logs-file-mock')
        self.log_collector.update(test_message)
        self.log_collector.logs_file.write.assert_called_once_with(
            logs.LogCollector.COMMON_LOG_FORMAT.format(message=test_message)
        )
        self.log_collector.logs_file.flush.assert_called_once_with()
