import os
import mock
import unittest
import subprocess

from docker_test_tools import environment

SERVICE_NAMES = ['consul.service', 'mocked.service']


class TestEnvironmentController(unittest.TestCase):
    """Test for the environment controller package."""

    COMPOSE_CONTENT = """
version: '2.1'
services:
  service1:
    image: image1
  service2:
    image: image2
    healthcheck:
        test: 'test'
"""
    ENVIRONMENT_VARIABLES = {'test': 'test'}

    def setUp(self):
        self.project_name = 'test-project'
        self.compose_path = 'test-compose-path'
        self.log_path = '/tmp/test-target-log-path'

        self.controller = self.get_controller()

    def tearDown(self):
        if os.path.exists(self.log_path):
            os.remove(self.log_path)

    @mock.patch("subprocess.check_output")
    def test_environment_general_methods_happy_flow(self, mocked_check_output):
        """Validate environment controller general methods behave as expected."""
        self.controller.run_containers()
        mocked_check_output.assert_called_with(
            ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'up', '--build', '-d'],
            stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
        )

        self.controller.kill_containers()
        mocked_check_output.assert_called_with(
            ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'kill'],
            stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
        )

        self.controller.remove_containers()
        mocked_check_output.assert_called_with(
            ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'rm', '-f'],
            stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
        )

    @mock.patch('docker_test_tools.environment.EnvironmentController.validate_service_name', mock.MagicMock())
    @mock.patch("subprocess.check_output")
    def test_container_methods_happy_flow(self, mocked_check_output):
        """Validate environment controller specific methods behave as expected."""
        service_name = 'test'

        self.controller.kill_container(service_name)
        mocked_check_output.assert_called_with(
            ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'kill', service_name],
            stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
        )

        self.controller.restart_container(service_name)
        mocked_check_output.assert_called_with(
            ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'restart', service_name],
            stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
        )

        self.controller.get_container_id(service_name)
        mocked_check_output.assert_called_with(
            ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'ps', '-q', service_name],
            stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
        )

        self.controller.pause_container(service_name)
        mocked_check_output.assert_called_with(
            ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'pause', service_name],
            stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
        )

        self.controller.unpause_container(service_name)
        mocked_check_output.assert_called_with(
            ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'unpause', service_name],
            stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
        )

        mock_get_id = mock.MagicMock(return_value='test-id')
        with mock.patch("docker_test_tools.environment.EnvironmentController.get_container_id", mock_get_id):
            mocked_check_output.return_value = '{"Health": {"Status":"healthy"}}'
            self.assertTrue(self.controller.is_container_ready('test'))
            mocked_check_output.assert_called_with(
                r"docker inspect --format='{{json .State}}' test-id",
                shell=True, stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
            )

            mocked_check_output.return_value = '{"Health": {"Status":"unhealthy"}}'
            self.assertFalse(self.controller.is_container_ready('test'))
            mocked_check_output.assert_called_with(
                r"docker inspect --format='{{json .State}}' test-id",
                shell=True, stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
            )

            mocked_check_output.return_value = '{"Status":"running"}'
            self.assertTrue(self.controller.is_container_ready('test'))
            mocked_check_output.assert_called_with(
                r"docker inspect --format='{{json .State}}' test-id",
                shell=True, stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
            )

            mocked_check_output.return_value = '{"Status":"not-running"}'
            self.assertFalse(self.controller.is_container_ready('test'))
            mocked_check_output.assert_called_with(
                r"docker inspect --format='{{json .State}}' test-id",
                shell=True, stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
            )

    @mock.patch('subprocess.check_output', mock.MagicMock(side_effect=subprocess.CalledProcessError(1, '', '')))
    @mock.patch('docker_test_tools.environment.EnvironmentController.validate_service_name', mock.MagicMock())
    def test_environment_compose_command_error(self):
        """Validate environment controller methods in cases compose command fails."""

        with self.assertRaises(RuntimeError):
            self.controller.run_containers()

        with self.assertRaises(RuntimeError):
            self.controller.kill_containers()

        with self.assertRaises(RuntimeError):
            self.controller.get_service_list()

        with self.assertRaises(RuntimeError):
            self.controller.get_containers_logs()

        with self.assertRaises(RuntimeError):
            self.controller.remove_containers()

        with self.assertRaises(RuntimeError):
            self.controller.kill_container('test')

        with self.assertRaises(RuntimeError):
            self.controller.restart_container('test')

        with self.assertRaises(RuntimeError):
            self.controller.pause_container('test')

        with self.assertRaises(RuntimeError):
            self.controller.unpause_container('test')

        with self.assertRaises(RuntimeError):
            self.controller.get_container_id('test')

        mock_get_id = mock.MagicMock(return_value='test-id')
        with mock.patch("docker_test_tools.environment.EnvironmentController.get_container_id", mock_get_id):
            self.assertFalse(self.controller.is_container_ready('test'))

    def test_container_methods_bad_service_name(self):
        """Validate environment controller methods fail in case of invalid service name."""
        service_name = 'invalid'
        with self.assertRaises(ValueError):
            self.controller.kill_container(service_name)

        with self.assertRaises(ValueError):
            self.controller.restart_container(service_name)

        with self.assertRaises(ValueError):
            self.controller.get_container_id(service_name)

        with self.assertRaises(ValueError):
            self.assertTrue(self.controller.is_container_ready(service_name))

    @mock.patch('docker_test_tools.environment.EnvironmentController.validate_service_name', mock.MagicMock())
    @mock.patch("docker_test_tools.environment.EnvironmentController.is_container_ready")
    @mock.patch("subprocess.check_output")
    def test_container_down(self, mocked_check_output, mock_is_ready):
        """Validate container_down context manager - without health check."""
        controller = self.get_controller()

        mock_is_ready.return_value = True
        with controller.container_down('service1'):
            mocked_check_output.assert_called_with(
                ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'kill', 'service1'],
                stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
            )

        mock_is_ready.assert_called_with('service1')
        mocked_check_output.assert_called_with(
            ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'restart', 'service1'],
            stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
        )

    @mock.patch('docker_test_tools.environment.EnvironmentController.validate_service_name', mock.MagicMock())
    @mock.patch("docker_test_tools.environment.EnvironmentController.is_container_ready")
    @mock.patch("subprocess.check_output")
    def test_container_paused(self, mocked_check_output, mock_is_ready):
        """Validate container_down context manager - without health check."""
        controller = self.get_controller()

        mock_is_ready.return_value = True
        with controller.container_paused('service1'):
            mocked_check_output.assert_called_with(
                ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'pause', 'service1'],
                stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
            )

        mock_is_ready.assert_called_with('service1')
        mocked_check_output.assert_called_with(
            ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'unpause', 'service1'],
            stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
        )

    @mock.patch('docker_test_tools.environment.EnvironmentController.kill_containers')
    @mock.patch('docker_test_tools.environment.EnvironmentController.remove_containers')
    @mock.patch('docker_test_tools.environment.EnvironmentController.run_containers')
    def test_setup(self, run_mock, remove_mock, kill_mock):
        """Validate the environment setup method."""
        self.controller.setup()
        kill_mock.assert_called_once_with()
        remove_mock.assert_called_once_with()
        run_mock.assert_called_once_with()

    @mock.patch('docker_test_tools.environment.EnvironmentController.teardown')
    @mock.patch('docker_test_tools.environment.EnvironmentController.kill_containers')
    @mock.patch('docker_test_tools.environment.EnvironmentController.remove_containers')
    @mock.patch('docker_test_tools.environment.EnvironmentController.run_containers')
    def test_setup_failure(self, run_mock, remove_mock, kill_mock, tear_down_mock):
        """Validate the environment setup method - failure scenario."""
        run_mock.side_effect = Exception('unexpected-error')

        with self.assertRaises(Exception):
            self.controller.setup()

        kill_mock.assert_called_once_with()
        remove_mock.assert_called_once_with()
        tear_down_mock.assert_called_once_with()

    @mock.patch('docker_test_tools.environment.EnvironmentController.kill_containers')
    @mock.patch('docker_test_tools.environment.EnvironmentController.remove_containers')
    @mock.patch('docker_test_tools.environment.EnvironmentController.get_containers_logs')
    def test_teardown(self, get_log_mock, remove_mock, kill_mock):
        """Validate the environment teardown method."""
        self.controller.teardown()
        kill_mock.assert_called_once_with()
        remove_mock.assert_called_once_with()
        get_log_mock.assert_called_once_with()

    @mock.patch('docker_test_tools.environment.EnvironmentController.get_services', mock.MagicMock())
    @mock.patch('docker_test_tools.environment.EnvironmentController.kill_containers')
    @mock.patch('docker_test_tools.environment.EnvironmentController.remove_containers')
    @mock.patch('docker_test_tools.environment.EnvironmentController.run_containers')
    def test_setup_with_reuse(self, run_mock, remove_mock, kill_mock):
        """Validate the environment setup method when container reuse is enabled."""

        controller = environment.EnvironmentController(compose_path=self.compose_path,
                                                       log_path=self.log_path,
                                                       reuse_containers=True,
                                                       project_name=self.project_name)
        controller.setup()
        kill_mock.assert_not_called()
        remove_mock.assert_not_called()
        run_mock.assert_called_once_with()

    @mock.patch('docker_test_tools.environment.EnvironmentController.get_services', mock.MagicMock())
    @mock.patch('docker_test_tools.environment.EnvironmentController.kill_containers')
    @mock.patch('docker_test_tools.environment.EnvironmentController.remove_containers')
    @mock.patch('docker_test_tools.environment.EnvironmentController.get_containers_logs')
    def test_teardown_with_reuse(self, get_log_mock, remove_mock, kill_mock):
        """Validate the environment teardown method when container reuse is enabled."""
        controller = environment.EnvironmentController(compose_path=self.compose_path,
                                                       log_path=self.log_path,
                                                       reuse_containers=True,
                                                       project_name=self.project_name)
        controller.teardown()
        kill_mock.assert_not_called()
        remove_mock.assert_not_called()
        get_log_mock.assert_called_once_with()

    @mock.patch('docker_test_tools.environment.EnvironmentController.get_service_list',
                mock.MagicMock(return_value=SERVICE_NAMES))
    def test_log_file_split(self):
        """Validate environment controller methods behave as expected."""
        with mock.patch("subprocess.check_output") as mocked_check_output:
            self.controller.get_containers_logs()
        for service_name in SERVICE_NAMES:
            service_command = "{service_name} | sed 's/^[^|]*| //'".format(
                service_name=service_name) if service_name else ''
            mocked_check_output.assert_any_call(
                'docker-compose -f {compose_path} -p {project_name} logs --no-color {service_command} > {log_path}'.format(
                    compose_path=self.compose_path,
                    project_name=self.project_name,
                    log_path=self.controller._get_service_log_file_name(service_name),
                    service_command=service_command),
                shell=True, stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
            )

    @mock.patch('docker_test_tools.environment.EnvironmentController._get_environment_variables',
                mock.MagicMock(return_value=ENVIRONMENT_VARIABLES))
    def get_controller(self):
        """Returns a new EnvironmentController."""
        with mock.patch("subprocess.check_output", return_value="service1\nservice2\n"):
            return environment.EnvironmentController(log_path=self.log_path,
                                                     compose_path=self.compose_path,
                                                     project_name=self.project_name)
