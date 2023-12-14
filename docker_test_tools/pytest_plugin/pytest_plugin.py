import os

import pytest

from docker_test_tools import config, environment


CHECKS_TIMEOUT = (
    1 * 60
)  # Used by docker-test-tools for health checks that services are up
CHECKS_INTERVAL = 1


@pytest.fixture(scope="session", name="controller_config")
def fixture_controller_config():
    """Docker test tools environment controller config to use.
    Can be overridden with file by setting the DOCKER_TEST_TOOLS_CONFIG_FILE environment variable.
    Can be overriden also by defining a fixture with the same name.
    """
    return config.Config(
        config_path=os.environ.get("DOCKER_TEST_TOOLS_CONFIG_FILE", None)
    )


@pytest.fixture(scope="session", name="controller")
def fixture_controller(controller_config):
    controller = environment.EnvironmentController(
        log_path=controller_config.log_path,
        project_name=controller_config.project_name,
        compose_path=controller_config.docker_compose_path,
        compose_command=controller_config.docker_compose_command,
        reuse_containers=controller_config.reuse_containers,
    )

    controller.setup()
    controller.update_plugins("========= PYTEST SESSION BEGINNING =========")

    yield controller

    controller.update_plugins("========= PYTEST SESSION END =========")
    controller.teardown()


@pytest.fixture(scope="session")
def wait_for_services(controller):
    """Wait for all services to be up."""
    assert controller.wait_for_services(
        interval=CHECKS_INTERVAL, timeout=CHECKS_TIMEOUT
    )


@pytest.fixture
def log_test_start_end(controller, request):
    """Write a test started/end log message to the main log file."""
    start_message = "========= TEST BEGINNING: {0} =========".format(request.node.nodeid)
    controller.update_plugins(start_message)

    yield

    end_message = "========= TEST END: {0} =========".format(request.node.nodeid)
    controller.update_plugins(end_message)
