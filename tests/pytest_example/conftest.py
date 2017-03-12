"""utilized by in pytest configuration."""
import os

import pytest

from docker_test_tools import config, environment

config = config.Config(config_path=os.environ.get('CONFIG', None))
controller = environment.EnvironmentController(log_path=config.log_path,
                                               project_name=config.project_name,
                                               compose_path=config.docker_compose_path,
                                               reuse_containers=config.reuse_containers)


@pytest.fixture(scope="session", autouse=True)
def global_setup_teardown():
    """This function will be executed once per testing session."""
    controller.setup()
    yield
    controller.teardown()
