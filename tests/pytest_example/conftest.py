"""utilized by in pytest configuration."""
import pytest

from docker_test_tools import EnvironmentLayer


@pytest.fixture(scope="session", autouse=True)
def global_setup_teardown():
    """This function will be executed once per testing session."""
    EnvironmentLayer.setUp()
    yield
    EnvironmentLayer.tearDown()
