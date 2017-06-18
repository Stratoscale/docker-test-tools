"""utilized by in pytest configuration."""
import pytest

from docker_test_tools.environment import EnvironmentController

controller = EnvironmentController.from_file(config_path='tests/integration/pytest.cfg')


@pytest.fixture(scope="session", autouse=True)
def global_setup_teardown():
    """This function will be executed once per testing session."""
    controller.setup()
    yield
    controller.teardown()


def pytest_runtest_setup(item):
    """Assign the controller as a test class member."""
    item.parent.obj.controller = controller
