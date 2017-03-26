"""utilized by in pytest configuration."""
import os

import pytest

from docker_test_tools import environment


@pytest.fixture(scope="session", autouse=True)
def global_setup_teardown():
    """This function will be executed once per testing session."""
    controller = environment.EnvironmentController.from_file(config_path=os.environ.get('CONFIG', None))
    controller.setup()
    yield
    controller.teardown()
