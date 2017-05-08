# Docker Test Tools
The `docker-test-tools` package makes it easy to write tests that relies on docker containers enviorement in order to operate.

#### Prerequisites
* The project under test must be [skipper](https://github.com/Stratoscale/skipper) compatible. 

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

For example: `test.cfg` (the section may also be included in `nose2.cfg`)
```cfg
[environment]
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
import httplib
import logging
import requests

from docker_test_tools.base_test import BaseDockerTest
from docker_test_tools.wiremock import WiremockController
from docker_test_tools.utils import get_curl_health_check


class ExampleTest(BaseDockerTest):
    """Usage example test for docker-test-tools."""

    # [OPTIONAL] User defined health checks, once defined the test setUp will wait for them to pass.
    REQUIRED_HEALTH_CHECKS = [
        get_curl_health_check(service_name='consul.service', url='http://consul.service:8500'),
        get_curl_health_check(service_name='mocked.service', url='http://mocked.service:9999/__admin')
    ]

    # [OPTIONAL] User defined health checks timeout
    CHECKS_TIMEOUT = 60

    def setUp(self):
        """Create a wiremock controller and add a cleanup for it."""
        super(ExampleTest, self).setUp()

        self.wiremock = WiremockController(url='http://mocked.service:9999')
        self.addCleanup(self.wiremock.reset_mapping)

    def test_services_sanity(self):
        """Validate services are responsive once the test start."""
        logging.info('Validating consul container is responsive')
        self.assertEquals(requests.get('http://consul.service:8500').status_code, httplib.OK)

        logging.info('Validating wiremock container is responsive')
        self.assertEquals(requests.get('http://mocked.service:9999/__admin').status_code, httplib.OK)

    def test_service_down(self):
        """Validate service down scenario."""
        logging.info('Validating consul container is responsive')
        self.assertEquals(requests.get('http://consul.service:8500').status_code, httplib.OK)

        logging.info('Validating consul container is unresponsive while in `container_down` context')
        with self.controller.container_down(name='consul.service'):
            with self.assertRaises(requests.ConnectionError):
                requests.get('http://consul.service:8500')

        logging.info('Validating consul container has recovered and is responsive')
        self.assertEquals(requests.get('http://consul.service:8500').status_code, httplib.OK)

    def test_service_paused(self):
        """Validate service paused scenario."""
        logging.info('Validating consul container is responsive')
        self.assertEquals(requests.get('http://consul.service:8500', timeout=2).status_code, httplib.OK)

        logging.info('Validating consul container is unresponsive while in `container_paused` context')
        with self.controller.container_paused(name='consul.service'):
            with self.assertRaises(requests.Timeout):
                requests.get('http://consul.service:8500', timeout=2)

        logging.info('Validating consul container has recovered and is responsive')
        self.assertEquals(requests.get('http://consul.service:8500', timeout=2).status_code, httplib.OK)

    def test_mocked_service_configuration(self):
        """Validate wiremock service."""
        logging.info('Validating mocked service fail to find `test` endpoint')
        self.assertEquals(requests.post('http://mocked.service:9999/test').status_code, httplib.NOT_FOUND)

        logging.info('Use WiremockController to stub the service `test` endpoint')
        stubs_dir_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'wiremock_stubs')
        self.wiremock.set_mapping_from_dir(stubs_dir_path)

        logging.info('Validating mocked service response on `test` endpoint')
        self.assertEquals(requests.post('http://mocked.service:9999/test').status_code, httplib.OK)

```

## Integrating With `nose2`
---
### Run the tests
```
$ CONFIG=test.cfg nose2 --config=test.cfg --verbose --project-directory .
```
Outcome:
```
Validate wiremock service. ... ok
test_service_down (tests.integration.test_example.ExampleTest)
Validate service down scenario. ... ok
test_service_paused (tests.integration.test_example.ExampleTest)
Validate service paused scenario. ... ok
test_services_sanity (tests.integration.test_example.ExampleTest)
Validate services are responsive once the test start. ... ok

----------------------------------------------------------------------
Ran 4 tests in 30.789s

OK
```

## Integrating With `pytest`
---
### Define a conftest.py File Describing The Required Fixture

```python
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

```

### Run the Tests
```
$ CONFIG=tests/pytest_example/test.cfg pytest tests/pytest_example/
```

Outcome:
```
==== ... ==== test session starts ==== ... ====
platform linux2 -- Python 2.7.13, pytest-3.0.6, py-1.4.33, pluggy-0.4.0 -- /usr/local/bin/python2
cachedir: .cache
rootdir: /home/sarbov/work/docker-test-tools, inifile: 
collected 4 items 

tests/integration/test_example.py::ExampleTest::test_mocked_service_configuration PASSED
tests/integration/test_example.py::ExampleTest::test_service_down PASSED
tests/integration/test_example.py::ExampleTest::test_service_paused PASSED
tests/integration/test_example.py::ExampleTest::test_services_sanity PASSED

==== ... ==== 4 passed in 32.02 seconds ==== ... ====
```
