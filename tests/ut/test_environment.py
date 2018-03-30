import os
import mock
import docker
import unittest
import subprocess

from waiting import TimeoutExpired
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
        self.controller.up()
        mocked_check_output.assert_called_with(
            ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'up', '--build', '-d'],
            stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
        )

        self.controller.down()
        mocked_check_output.assert_called_with(
            ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'down'],
            stderr=subprocess.STDOUT, env=self.ENVIRONMENT_VARIABLES
        )

    def test_container_methods_happy_flow(self):
        """Validate environment controller specific methods behave as expected."""
        test_id = '111111'
        service_name = 'service1'

        with mock.patch.object(docker.APIClient, 'containers') as mock_containers:
            mock_containers.return_value = [{'Labels': {'com.docker.compose.project': self.project_name},
                                             'Id': 'container-id'}]
            self.controller.get_container_id(service_name)
            mock_containers.assert_called_with(filters={'label': 'com.docker.compose.service=service1'})

        with mock.patch('docker_test_tools.environment.EnvironmentController.get_container_id',
                        mock.MagicMock(return_value=test_id)):
            with mock.patch.object(docker.APIClient, 'kill') as mock_kill:
                self.controller.kill_container(service_name)
                mock_kill.assert_called_with(test_id)

            with mock.patch.object(docker.APIClient, 'restart') as mock_restart:
                self.controller.restart_container(service_name)
                mock_restart.assert_called_with(test_id)

            with mock.patch.object(docker.APIClient, 'pause') as mock_pause:
                self.controller.pause_container(service_name)
                mock_pause.assert_called_with(test_id)

            with mock.patch.object(docker.APIClient, 'unpause') as mock_unpause:
                self.controller.unpause_container(service_name)
                mock_unpause.assert_called_with(test_id)

            with mock.patch.object(docker.APIClient, 'start') as mock_start:
                self.controller.start_container(service_name)
                mock_start.assert_called_with(test_id)

            with mock.patch.object(docker.APIClient, 'stop') as mock_stop:
                self.controller.stop_container(service_name)
                mock_stop.assert_called_with(test_id)

            with mock.patch.object(docker.APIClient, 'inspect_container') as mock_inspect:
                self.controller.inspect_container(service_name)
                mock_inspect.assert_called_with(test_id)

            with mock.patch.object(docker.APIClient, 'inspect_container',
                                   return_value={"State": {"Health": {"Status": "healthy"}}}):
                self.assertTrue(self.controller.is_container_ready('test'))

            with mock.patch.object(docker.APIClient, 'inspect_container',
                                   return_value={"State": {"Health": {"Status": "unhealthy"}}}):
                self.assertFalse(self.controller.is_container_ready('test'))

            with mock.patch.object(docker.APIClient, 'inspect_container',
                                   return_value={"State": {"Status": "running"}}):
                self.assertTrue(self.controller.is_container_ready('test'))

            with mock.patch.object(docker.APIClient, 'inspect_container',
                                   return_value={"State": {"Status": "not-running"}}):
                self.assertFalse(self.controller.is_container_ready('test'))

    @mock.patch('subprocess.check_output', mock.MagicMock(side_effect=subprocess.CalledProcessError(1, '', '')))
    @mock.patch('docker_test_tools.environment.EnvironmentController.validate_service_name', mock.MagicMock())
    def test_environment_compose_command_error(self):
        """Validate environment controller methods in cases compose command fails."""

        with self.assertRaises(RuntimeError):
            self.controller.up()

        with self.assertRaises(RuntimeError):
            self.controller.down()

        with self.assertRaises(RuntimeError):
            self.controller.get_services()

        with self.assertRaises(RuntimeError):
            self.controller.restart_container('test')

        with self.assertRaises(RuntimeError):
            self.controller.pause_container('test')

        with self.assertRaises(RuntimeError):
            self.controller.unpause_container('test')

        with self.assertRaises(RuntimeError):
            self.controller.stop_container('test')

        with self.assertRaises(RuntimeError):
            self.controller.start_container('test')

        with self.assertRaises(RuntimeError):
            self.controller.get_container_id('test')

        mock_get_id = mock.MagicMock(return_value='test-id')
        with mock.patch("docker_test_tools.environment.EnvironmentController.get_container_id", mock_get_id):
            self.controller.docker_client.inspect_container = mock.MagicMock(return_value={
                "State": {
                    "Status": "not-running"
                }
            })
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

    @mock.patch("docker_test_tools.environment.EnvironmentController.is_container_ready")
    def test_container_down(self, mock_is_ready):
        """Validate container_down context manager - without health check."""
        test_id = '222222'
        mock_is_ready.return_value = True

        with mock.patch("docker_test_tools.environment.EnvironmentController.get_container_id", return_value=test_id):
            with mock.patch.object(docker.APIClient, 'kill') as mock_kill:
                with mock.patch.object(docker.APIClient, 'restart')as mock_restart:
                    with self.controller.container_down('service1'):
                        mock_kill.assert_called_with(test_id)

                    mock_is_ready.assert_called_with('service1')
                    mock_restart.assert_called_with(test_id)

    @mock.patch("docker_test_tools.environment.EnvironmentController.is_container_ready")
    def test_container_paused(self, mock_is_ready):
        """Validate container_paused context manager - without health check."""
        test_id = '333333'
        mock_is_ready.return_value = True

        with mock.patch("docker_test_tools.environment.EnvironmentController.get_container_id", return_value=test_id):
            with mock.patch.object(docker.APIClient, 'pause') as mock_pause:
                with mock.patch.object(docker.APIClient, 'unpause')as mock_unpause:
                    with self.controller.container_paused('service1'):
                        mock_pause.assert_called_with(test_id)

                    mock_is_ready.assert_called_with('service1')
                    mock_unpause.assert_called_with(test_id)

    @mock.patch("docker_test_tools.environment.EnvironmentController.is_container_ready")
    def test_container_stopped(self, mock_is_ready):
        """Validate container_stopped context manager - without health check."""
        test_id = '333333'
        mock_is_ready.return_value = True

        with mock.patch("docker_test_tools.environment.EnvironmentController.get_container_id", return_value=test_id):
            with mock.patch.object(docker.APIClient, 'stop') as mock_stop:
                with mock.patch.object(docker.APIClient, 'start')as mock_start:
                    with self.controller.container_stopped('service1'):
                        mock_stop.assert_called_with(test_id)

                    mock_is_ready.assert_called_with('service1')
                    mock_start.assert_called_with(test_id)

    @mock.patch('docker_test_tools.environment.EnvironmentController.down')
    @mock.patch('docker_test_tools.environment.EnvironmentController.up')
    @mock.patch('docker_test_tools.logs.LogCollector.start')
    def test_setup(self, start_collection_mock, up_mock, down_mock):
        """Validate the environment setup method."""
        self.controller.setup()
        down_mock.assert_called_once_with()
        up_mock.assert_called_once_with()
        start_collection_mock.assert_called_once_with()

    @mock.patch('docker_test_tools.environment.EnvironmentController.teardown')
    @mock.patch('docker_test_tools.environment.EnvironmentController.down')
    @mock.patch('docker_test_tools.environment.EnvironmentController.up')
    def test_setup_failure(self, up_mock, down_mock, tear_down_mock):
        """Validate the environment setup method - failure scenario."""
        up_mock.side_effect = Exception('unexpected-error')

        with self.assertRaises(Exception):
            self.controller.setup()

        down_mock.assert_called_once_with()
        tear_down_mock.assert_called_once_with()

    @mock.patch('docker_test_tools.environment.EnvironmentController.get_services', mock.MagicMock())
    @mock.patch('docker_test_tools.environment.EnvironmentController.down')
    @mock.patch('docker_test_tools.logs.LogCollector.stop')
    def test_teardown(self, stop_collection_mock, down_mock):
        """Validate the environment teardown method."""
        self.controller.teardown()
        down_mock.assert_called_once_with()
        stop_collection_mock.assert_called_once_with()

    @mock.patch('docker_test_tools.environment.EnvironmentController.get_services', mock.MagicMock())
    @mock.patch('docker_test_tools.environment.EnvironmentController.down')
    @mock.patch('docker_test_tools.environment.EnvironmentController.up')
    @mock.patch('docker_test_tools.logs.LogCollector.start')
    def test_setup_with_reuse(self, start_collection_mock, up_mock, down_mock):
        """Validate the environment setup method when container reuse is enabled."""

        controller = environment.EnvironmentController(compose_path=self.compose_path,
                                                       log_path=self.log_path,
                                                       reuse_containers=True,
                                                       project_name=self.project_name)
        controller.setup()
        down_mock.assert_not_called()
        up_mock.assert_called_once_with()
        start_collection_mock.assert_called_once_with()

    @mock.patch('docker_test_tools.environment.EnvironmentController.get_services', mock.MagicMock())
    @mock.patch('docker_test_tools.environment.EnvironmentController.down')
    @mock.patch('docker_test_tools.logs.LogCollector.stop')
    def test_teardown_with_reuse(self, stop_collection_mock, down_mock):
        """Validate the environment teardown method when container reuse is enabled."""
        controller = environment.EnvironmentController(compose_path=self.compose_path,
                                                       log_path=self.log_path,
                                                       reuse_containers=True,
                                                       project_name=self.project_name)
        controller.teardown()
        down_mock.assert_not_called()
        stop_collection_mock.assert_called_once_with()

    @mock.patch('docker_test_tools.environment.EnvironmentController.is_container_ready')
    def test_wait_for_services(self, mock_is_container_ready):
        """Validate the environment wait_for_services method."""
        controller = self.get_controller()
        mock_is_container_ready.return_value = True
        self.assertTrue(controller.wait_for_services())
        mock_is_container_ready.assert_has_calls([mock.call('service1'), mock.call('service2')], any_order=True)
        mock_is_container_ready.side_effect = TimeoutExpired(timeout_seconds=1, what='something')
        self.assertFalse(controller.wait_for_services())

    def test_from_file(self):
        """"Validate the environment from_file method."""
        mocked_config = mock.MagicMock(log_path='test-log-path',
                                       project_name='test-project-name',
                                       reuse_containers='test-reuse-containers',
                                       docker_compose_path='test-docker-compose-path')

        with mock.patch("subprocess.check_output", return_value="service1\nservice2\n"):
            with mock.patch("docker_test_tools.config.Config", return_value=mocked_config):
                controller = environment.EnvironmentController.from_file('some-path')

        self.assertEqual(controller.log_path, mocked_config.log_path)
        self.assertEqual(controller.project_name, mocked_config.project_name)
        self.assertEqual(controller.compose_path, mocked_config.docker_compose_path)
        self.assertEqual(controller.reuse_containers, mocked_config.reuse_containers)

    @mock.patch('docker_test_tools.environment.EnvironmentController._get_environment_variables',
                mock.MagicMock(return_value=ENVIRONMENT_VARIABLES))
    def get_controller(self):
        """Returns a new EnvironmentController."""
        with mock.patch("subprocess.check_output", return_value="service1\nservice2\n"):
            return environment.EnvironmentController(log_path=self.log_path,
                                                     compose_path=self.compose_path,
                                                     project_name=self.project_name)
