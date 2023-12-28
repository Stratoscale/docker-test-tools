# Docker Test Tools
The `docker-test-tools` package makes it easy to write tests that relies on docker containers environment in order to operate.

#### Features
* Manage container operation easily within the tests.
* Setup and tear down containers environment as part of the tests run flow.
* Integrated with [nose2](https://nose2.readthedocs.io/en/latest/index.html) and [pytest](http://doc.pytest.org/en/latest/) test runners.
* Integrated with [wiremock](http://wiremock.org/).


## Setup

### Define a Docker Compose File Describing the Required Environment

For example: `docker-compose.yml`
```yml
version: '2.1'

networks:
  tests-network:
    driver: bridge

services:

  consul.service:
    image: consul
    networks: [tests-network]

    # [OPTIONAL] healthcheck definition requires docker version > 1.12.
    healthcheck:
      test: "curl -f http://localhost:8500 || false"
      interval: 1s
      retries: 120

  mocked.service:
    image: stratoscale/wiremock:latest
    networks: [tests-network]
    command: "9999"

    # [OPTIONAL] healthcheck definition requires docker version > 1.12.
    healthcheck:
      test: "curl -f http://localhost:9999/__admin || false"
      interval: 1s
      retries: 120
```

### Define the Environment Configuration File
Under an `[environment]` section, define:
* `log-path`: Docker logs path. 
* `project-name`: Compose project name.
* `docker-compose-path`: Docker compose file path.
* `reuse-containers`: Whether or not to keep containers between test runs [True/ False].
* `collect-stats`: Whether or not to save containers stats [True/ False].

For example: `test.cfg` (the section may also be included in `nose2.cfg`)
```cfg
[environment]
always-on = True
collect-stats = True
project-name = test
reuse-containers = False
log-path = docker-tests.log
docker-compose-path = tests/docker-compose.yml
```
> **NOTE**: You may override configurations using environment variables (`DTT_PROJECT_NAME`, `DTT_REUSE_CONTAINERS`, `DTT_LOG_PATH`, `DTT_COMPOSE_PATH`).

> **NOTE**: Make sure you configure your `skipper.yml` with the proper `build-container-net` option, based on the `project-name` and `network`.
e.g `build-container-net: test_tests-network`

### Define Tests Based on `DockerBaseTest`

For example: `test_example.py`
```python
import os
import logging
import requests

from six.moves import http_client

from docker_test_tools.utils import get_health_check
from docker_test_tools.base_test import BaseDockerTest
from docker_test_tools.wiremock import WiremockController

log = logging.getLogger(__name__)

CONSUL_URL = "http://localhost:8500"
WIREMOCK_URL = "http://localhost:9999"

# Define health check functions for the environment services
consul_health_check = get_health_check('consul.service', url=CONSUL_URL)
mock_service_health_check = get_health_check('mocked.service', url=WIREMOCK_URL + '/__admin')


class ExampleTest(BaseDockerTest):
    """Usage example test for docker-test-tools."""

    # [OPTIONAL] User defined health checks, once defined the test setUp will wait for them to pass.
    REQUIRED_HEALTH_CHECKS = [consul_health_check,
                              mock_service_health_check]

    # [OPTIONAL] User defined health checks timeout
    CHECKS_TIMEOUT = 10

    def setUp(self):
        """Create a wiremock controller and add a cleanup for it."""
        super(ExampleTest, self).setUp()

        self.wiremock = WiremockController(url=WIREMOCK_URL)
        self.addCleanup(self.wiremock.reset_mapping)

    def test_services_sanity(self):
        """Validate services are responsive once the test start."""
        log.info('Validating consul container is responsive')
        self.assertEquals(requests.get(CONSUL_URL).status_code, http_client.OK)

        log.info('Validating wiremock container is responsive')
        self.assertEquals(requests.get(WIREMOCK_URL + '/__admin').status_code, http_client.OK)

    def test_service_down(self):
        """Validate service down scenario."""
        log.info('Validating consul container is responsive')
        self.assertEquals(requests.get(CONSUL_URL).status_code, http_client.OK)

        log.info('Validating consul container is unresponsive while in `container_down` context')
        with self.controller.container_down(name='consul.service', health_check=consul_health_check):
            with self.assertRaises(requests.ConnectionError):
                requests.get(CONSUL_URL)

        log.info('Validating consul container has recovered and is responsive')
        self.assertEquals(requests.get(CONSUL_URL).status_code, http_client.OK)

    def test_service_stopped(self):
        """Validate service stopped scenario."""
        log.info('Validating consul container is responsive')
        self.assertEquals(requests.get(CONSUL_URL).status_code, http_client.OK)

        log.info('Validating consul container is unresponsive while in `container_stopped` context')
        with self.controller.container_stopped(name='consul.service', health_check=consul_health_check):
            with self.assertRaises(requests.ConnectionError):
                requests.get(CONSUL_URL)

        log.info('Validating consul container has recovered and is responsive')
        self.assertEquals(requests.get(CONSUL_URL).status_code, http_client.OK)

    def test_service_paused(self):
        """Validate service paused scenario."""
        log.info('Validating consul container is responsive')
        self.assertEquals(requests.get(CONSUL_URL, timeout=2).status_code, http_client.OK)

        log.info('Validating consul container is unresponsive while in `container_paused` context')
        with self.controller.container_paused(name='consul.service', health_check=consul_health_check):
            with self.assertRaises(requests.Timeout):
                requests.get(CONSUL_URL, timeout=2)

        log.info('Validating consul container has recovered and is responsive')
        self.assertEquals(requests.get(CONSUL_URL, timeout=2).status_code, http_client.OK)

    def test_mocked_service_configuration(self):
        """Validate wiremock service."""
        log.info('Validating mocked service fail to find `test` endpoint')
        self.assertEquals(requests.post(WIREMOCK_URL + '/test').status_code, http_client.NOT_FOUND)

        log.info('Use WiremockController to stub the service `test` endpoint')
        stubs_dir_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'wiremock_stubs')
        self.wiremock.set_mapping_from_dir(stubs_dir_path)

        log.info('Validating mocked service response on `test` endpoint')
        self.assertEquals(requests.post(WIREMOCK_URL + '/test').status_code, http_client.OK)
```

## Integrating With `nose2`
---
### Enable the plugin

In your `nose2.cfg` file, under the `unittest` section add `docker_test_tools` to the `plugins` list.

For example:

```cfg
[unittest]
plugins = docker_test_tools.plugin
```

### Run the tests
```
$ nose2 --config=test.cfg --verbose --project-directory .
```
Outcome:
```
test_mocked_service_configuration (tests.integration.test_example.ExampleTest)
Validate wiremock service. ... ok
test_service_down (tests.integration.test_example.ExampleTest)
Validate service down scenario. ... ok
test_service_paused (tests.integration.test_example.ExampleTest)
Validate service paused scenario. ... ok
test_service_stopped (tests.integration.test_example.ExampleTest)
Validate service down scenario. ... ok
test_services_sanity (tests.integration.test_example.ExampleTest)
Validate services are responsive once the test start. ... ok

----------------------------------------------------------------------
Ran 5 tests in 31.844s

OK
```

## Integrating With `pytest`
---
### Define a conftest.py File Describing The Required Fixture

```python
import pytest

from docker_test_tools import config


# define a fixture to override the default controller configuration
# default configuration file is defined by `DOCKER_TEST_TOOLS_CONFIG_FILE environment variable`
@pytest.fixture(scope="session", name="controller_config")
def fixture_controller_config():
    return config.Config(config_path="tests/integration/pytest.cfg")


# wait for services to be responsive before running the tests
# this fixture will automatically enable the plugin and create the `controller` fixture
@pytest.fixture(scope="session", autouse=True)
def fixture_wait(wait_for_services):
    """Run prior to any test - setup the environment."""
    _ = wait_for_services


# write test begin/end markers to the logs
@pytest.fixture(autouse=True)
def log_start_end(log_test_start_end):
    """Write a test started/end log message to all logs."""
    _ = log_test_start_end

    
# inject the controller instance to the unittest.TestCase
@pytest.fixture(scope="class")
def setup_controller(controller, request):
    """Run on test class setup.

    - Assign the controller object to the test.
    """
    request.cls.controller = controller
```

### Use services controller fixture in tests
```python

def test_services_sanity(controller):
    # take consul.service down
    controller.container_down(name='consul.service')

    # verify the system is still responsive
    ...
    
    # bring consul.service up
    controller.container_up(name='consul.service')
```


### Run the Tests
```
$ pytest tests/pytest_example/
```

Outcome:
```
==== ... ==== test session starts ==== ... ====
platform linux2 -- Python 2.7.13, pytest-3.0.6, py-1.4.33, pluggy-0.4.0 -- /usr/local/bin/python2
...
collected 5 items 

tests/integration/test_example.py::ExampleTest::test_mocked_service_configuration PASSED
tests/integration/test_example.py::ExampleTest::test_service_down PASSED
tests/integration/test_example.py::ExampleTest::test_service_paused PASSED
tests/integration/test_example.py::ExampleTest::test_service_stopped PASSED
tests/integration/test_example.py::ExampleTest::test_services_sanity PASSED

==== ... ==== 5 passed in 34.76 seconds ==== ... ====
```
