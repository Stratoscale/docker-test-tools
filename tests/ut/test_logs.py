import mock
import unittest

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
        self.log_collector = logs.LogCollector(
            log_path=self.TEST_LOG_PATH,
            encoding=self.TEST_ENCODING,
            project_name=self.TEST_PROJECT_NAME,
            compose_path=self.TEST_COMPOSE_PATH,
            environment_variables=self.TEST_ENVIRONMENT_VARIABLES,
        )

    @mock.patch("io.open")
    @mock.patch("subprocess.Popen")
    def test_start(self, mock_popen, mock_open):
        """"Validate the log collector start method."""
        mock_test_file = 'test-log-file'
        mock_test_process = 'test-log-process'

        mock_open.return_value = mock_test_file
        mock_popen.return_value = mock_test_process

        self.log_collector.start()
        mock_open.assert_called_with(self.TEST_LOG_PATH, 'w', encoding=self.TEST_ENCODING)
        mock_popen.assert_called_with(
            ['docker-compose',
             '-f', self.TEST_COMPOSE_PATH,
             '-p', self.TEST_PROJECT_NAME,
             'logs', '--no-color', '-f', '-t'],
            stdout=mock_test_file,
            env=self.TEST_ENVIRONMENT_VARIABLES
        )

        self.assertEqual(self.log_collector.logs_file, mock_test_file)
        self.assertEqual(self.log_collector.logs_process, mock_test_process)

    @mock.patch('docker_test_tools.logs.LogCollector._split_logs')
    def test_stop(self, mock_split_logs):
        """"Validate the log collector stop method."""
        self.log_collector.logs_file = mock.MagicMock(name='logs-file-mock')
        self.log_collector.logs_process = mock.MagicMock(name='logs-process-mock')
        self.log_collector.stop()

        self.log_collector.logs_process.kill.assert_called_once_with()
        self.log_collector.logs_process.wait.assert_called_once_with()
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
