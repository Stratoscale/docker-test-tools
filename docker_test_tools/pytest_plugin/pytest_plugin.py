import os

import pytest

from docker_test_tools import config, environment


CHECKS_TIMEOUT = (
    1 * 60
)  # Used by docker-test-tools for health checks that services are up
CHECKS_INTERVAL = 1


@pytest.fixture(scope="session")
def controller_config():
    """Docker test tools environment controller config to use.
    Can be overridden with file by setting the DOCKER_TEST_TOOLS_CONFIG_FILE environment variable.
    Can be overriden also by defining a fixture with the same name.
    """
    return config.Config(config_path=os.environ.get("DOCKER_TEST_TOOLS_CONFIG_FILE", None))


@pytest.fixture(scope="session")
def controller(controller_config):
    controller = environment.EnvironmentController(
        log_path=controller_config.log_path,
        project_name=controller_config.project_name,
        compose_path=controller_config.docker_compose_path,
        compose_command=controller_config.docker_compose_command,
        reuse_containers=controller_config.reuse_containers,
    )

    controller.setup()
    yield controller
    controller.teardown()


@pytest.fixture(scope="session")
def wait_for_services(controller):
    assert controller.wait_for_services(
        interval=CHECKS_INTERVAL, timeout=CHECKS_TIMEOUT
    )
