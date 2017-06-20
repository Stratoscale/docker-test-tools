# pylint: disable=unused-argument
from nose2.events import Plugin

from docker_test_tools.config import Config
from docker_test_tools.environment import EnvironmentController


class EnvironmentPlugin(Plugin):
    """Nose2 plugin, used for managing docker environment operations."""
    configSection = 'environment'
    commandLineSwitch = (None, 'environment', 'Enable docker test tools environment')

    def __init__(self, *args, **kwargs):
        self.controller = None
        super(EnvironmentPlugin, self).__init__(*args, **kwargs)

    def startTestRun(self, event):
        """Sets up the environment using docker commands."""
        config = Config(
            log_path=self.config.as_str('log-path', Config.DEFAULT_LOG_PATH),
            project_name=self.config.as_str('project-name', Config.DEFAULT_PROJECT_NAME),
            reuse_containers=self.config.as_bool('reuse-containers', Config.DEFAULT_REUSE_CONTAINERS),
            docker_compose_path=self.config.as_str('docker-compose-path', Config.DEFAULT_DOCKER_COMPOSE_PATH)
        )
        self.controller = EnvironmentController(
            log_path=config.log_path,
            project_name=config.project_name,
            compose_path=config.docker_compose_path,
            reuse_containers=config.reuse_containers,
        )
        self.controller.setup()

    def startTest(self, event):
        """Assign the controller object to the test."""
        event.test.controller = self.controller

    def stopTestRun(self, event):
        """Tears down the environment using docker commands."""
        if self.controller:
            self.controller.teardown()
