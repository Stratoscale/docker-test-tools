import os
import mock
import unittest
import subprocess

from docker_test_tools import environment


class TestEnvironmentController(unittest.TestCase):
    """Test for the environment controller package."""

    def setUp(self):

        self.project_name = 'test-project'
        self.compose_path = 'test-compose-path'
        self.log_path = '/tmp/test-target-log-path'

        self.controller = environment.EnvironmentController(log_path=self.log_path,
                                                            compose_path=self.compose_path,
                                                            project_name=self.project_name)

    def tearDown(self):
        if os.path.exists(self.log_path):
            os.remove(self.log_path)

    def test_environment_methods_happy_flow(self):
        """Validate environment controller methods behave as expected."""
        with mock.patch("subprocess.check_output") as mocked_check_output:
            self.controller.run_containers()
            mocked_check_output.assert_called_with(
                ['docker-compose', '-f', self.compose_path,  '-p', self.project_name, 'up', '--build', '-d'],
                stderr=subprocess.STDOUT
            )

            self.controller.kill_containers()
            mocked_check_output.assert_called_with(
                ['docker-compose', '-f', self.compose_path,  '-p', self.project_name, 'kill'],
                stderr=subprocess.STDOUT
            )

            self.controller.remove_containers()
            mocked_check_output.assert_called_with(
                ['docker-compose', '-f', self.compose_path,  '-p', self.project_name, 'rm', '-f'],
                stderr=subprocess.STDOUT
            )

            self.controller.get_containers_logs()
            mocked_check_output.assert_called_with(
                'docker-compose -f {compose_path} -p {project_name} logs --no-color > {log_path}'.format(
                    compose_path=self.compose_path, project_name=self.project_name,log_path=self.log_path),
                shell=True, stderr=subprocess.STDOUT
            )

    def test_environment_bad_arguments(self):
        """Validate environment controller methods fail when given bad arguments."""
        with self.assertRaises(RuntimeError):
            self.controller.run_containers()

        with self.assertRaises(RuntimeError):
            self.controller.kill_containers()

        with self.assertRaises(RuntimeError):
            self.controller.get_containers_logs()

        with self.assertRaises(RuntimeError):
            self.controller.remove_containers()

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