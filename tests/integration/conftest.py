"""utilized by in pytest configuration."""
from docker_test_tools.environment import EnvironmentController

controller = EnvironmentController.from_file(config_path='tests/integration/pytest.cfg')


def pytest_configure(config):
    """Run prior to any test - setup the environment."""
    controller.setup()


def pytest_unconfigure(config):
    """Run post all tests - tear down the environment."""
    controller.teardown()


def pytest_runtest_setup(item):
    """Run on test start.

    - Assign the controller object to the test.
    - Write a test started log message to the main log file.
    """
    item.parent.obj.controller = controller
    controller.update_plugins(item.nodeid)
