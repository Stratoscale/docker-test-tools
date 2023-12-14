"""utilized by in pytest configuration."""

import pytest

from docker_test_tools import config


@pytest.fixture(scope="session", name="controller_config")
def fixture_controller_config():
    return config.Config(config_path="tests/integration/pytest.cfg")


@pytest.fixture(scope="session", autouse=True)
def fixture_wait(wait_for_services):
    """Run prior to any test - setup the environment."""
    _ = wait_for_services


@pytest.fixture(scope="class")
def setup_controller(controller, request):
    """Run on test class setup.

    - Assign the controller object to the test.
    """
    request.cls.controller = controller


@pytest.fixture(autouse=True)
def log_start_end(log_test_start_end):
    """Write a test started/end log message to all logs."""
    _ = log_test_start_end
