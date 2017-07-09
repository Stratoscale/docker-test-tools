import os
import mock
import shutil
import tempfile
import unittest

from six.moves import configparser

from docker_test_tools.config import Config


class TestConfig(unittest.TestCase):
    """Test for the config class."""

    def setUp(self):
        """Create a temporary directory."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Remove the temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_happy_flow_no_file(self):
        """Create a config object validate operation success."""
        config = Config()

        self.assertEquals(config.log_path, Config.DEFAULT_LOG_PATH)
        self.assertEquals(config.project_name, Config.DEFAULT_PROJECT_NAME)
        self.assertEquals(config.reuse_containers, Config.DEFAULT_REUSE_CONTAINERS)
        self.assertEquals(config.docker_compose_path, Config.DEFAULT_DOCKER_COMPOSE_PATH)

    def test_happy_flow_using_file(self):
        """Parse a valid config file and validate operation success."""
        test_config = {Config.REUSE_CONTAINERS_OPTION: True,
                       Config.LOG_PATH_OPTION: 'test-log-path',
                       Config.PROJECT_NAME_OPTION: 'test-project',
                       Config.DOCKER_COMPOSE_PATH_OPTION: 'test-docker-compose-path'}

        test_config_path = self.create_config_file(config_input=test_config)
        config = Config(config_path=test_config_path)

        self.assertEquals(config.log_path, test_config[Config.LOG_PATH_OPTION])
        self.assertEquals(config.project_name, test_config[Config.PROJECT_NAME_OPTION])
        self.assertEquals(config.reuse_containers, test_config[Config.REUSE_CONTAINERS_OPTION])
        self.assertEquals(config.docker_compose_path, test_config[Config.DOCKER_COMPOSE_PATH_OPTION])

    def test_happy_flow_using_env_vars(self):
        """Set the env vars and validate operation success."""
        test_config = {Config.REUSE_CONTAINERS_ENV_VAR: 1,
                       Config.LOG_PATH_ENV_VAR: 'test-log-path',
                       Config.PROJECT_NAME_ENV_VAR: 'test-project',
                       Config.DOCKER_COMPOSE_PATH_ENV_VAR: 'test-docker-compose-path'}

        with mock.patch('os.environ.get', test_config.get):

            config = Config()

            self.assertEquals(config.log_path, test_config[Config.LOG_PATH_ENV_VAR])
            self.assertEquals(config.project_name, test_config[Config.PROJECT_NAME_ENV_VAR])
            self.assertEquals(config.reuse_containers, test_config[Config.REUSE_CONTAINERS_ENV_VAR])
            self.assertEquals(config.docker_compose_path, test_config[Config.DOCKER_COMPOSE_PATH_ENV_VAR])

    def test_missing_optional_option(self):
        """Parse a valid config file, with missing optional options and validate operation success."""
        test_config = {Config.DOCKER_COMPOSE_PATH_OPTION: 'test-docker-compose-path'}

        expected_config = {Config.LOG_PATH_OPTION: Config.DEFAULT_LOG_PATH,
                           Config.DOCKER_COMPOSE_PATH_OPTION: 'test-docker-compose-path',
                           Config.REUSE_CONTAINERS_OPTION: Config.DEFAULT_REUSE_CONTAINERS}

        test_config_path = self.create_config_file(config_input=test_config)

        config = Config(config_path=test_config_path)

        self.assertEquals(config.log_path, expected_config[Config.LOG_PATH_OPTION])
        self.assertEquals(config.reuse_containers, expected_config[Config.REUSE_CONTAINERS_OPTION])
        self.assertEquals(config.docker_compose_path, expected_config[Config.DOCKER_COMPOSE_PATH_OPTION])

    def test_bad_config_path(self):
        """Try parsing an invalid config file path and validate operation failure."""
        with self.assertRaises(RuntimeError):
            Config(config_path='bad-path')

    def test_bad_section_name(self):
        """Try parsing an invalid config file path and validate operation failure."""
        test_config_path = self.create_config_file(config_input={}, section='bad')
        with self.assertRaises(configparser.NoSectionError):
            Config(config_path=test_config_path)

    def create_config_file(self, config_input, section='environment'):
        """Create a config file based on the given dictionary."""
        test_config_path = os.path.join(self.test_dir, 'test.txt')

        parser = configparser.ConfigParser()

        with open(test_config_path, 'w') as cfgfile:
            parser.add_section(section)
            for option, value in config_input.items():
                parser.set(section, option, str(value))
            parser.write(cfgfile)

        return test_config_path
