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
    controller.write_common_log_message("TEST STARTED: {test_id}".format(test_id=item.nodeid))


def pytest_runtest_teardown(item):
    """"Run on test stop.

    - Write a test ended log message to the main log file.
    """
    controller.write_common_log_message("TEST ENDED: {test_id}".format(test_id=item.nodeid))
