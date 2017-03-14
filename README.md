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
version: '2'

networks:
  tests-network:
    driver: bridge

services:

  consul.service:
    image: consul
    networks: [tests-network]

  mocked.service:
    image: rackattack-nas.dc1:5000/wiremock:e069b8c8ba964a72daf08ad9c01c9147571dc2b5
    networks: [tests-network]
    command: "9999"
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

import docker_test_tools as dtt


class ExampleTest(dtt.BaseDockerTest):
    """Usage example test for docker-test-tools."""
    CONSUL_SERVICE_NAME = 'consul.service'
    MOCKED_SERVICE_NAME = 'mocked.service'

    CONSUL_URL = 'http://consul.service:8500'
    MOCKED_SERVICE_URL = 'http://mocked.service:9999'

    # Define the required services health checks to pass up before the test starts running
    REQUIRED_HEALTH_CHECKS = [
        dtt.get_curl_health_check(service_name=CONSUL_SERVICE_NAME, url=CONSUL_URL),
        dtt.get_curl_health_check(service_name=MOCKED_SERVICE_NAME, url=MOCKED_SERVICE_URL)
    ]

    def test_services_sanity(self):
        """Validate services are responsive once the test context start."""
        logging.info('Validating consul container is responsive')
        consul_response = requests.get(self.CONSUL_URL)
        self.assertEquals(consul_response.status_code, httplib.OK)

    def test_service_down(self):
        """Validate service down scenario."""
        logging.info('Validating consul container is responsive')
        consul_response = requests.get(self.CONSUL_URL)
        self.assertEquals(consul_response.status_code, httplib.OK)

        logging.info('Validating consul container is unresponsive while in `container_down` context')
        consul_health_check = dtt.get_curl_health_check(service_name=self.CONSUL_SERVICE_NAME, url=self.CONSUL_URL)
        with self.controller.container_down(name=self.CONSUL_SERVICE_NAME, health_check=consul_health_check):
            with self.assertRaises(requests.ConnectionError):
                requests.get(self.CONSUL_URL)

        logging.info('Validating consul container has recovered and is responsive')
        consul_response = requests.get(self.CONSUL_URL)
        self.assertEquals(consul_response.status_code, httplib.OK)

    def test_mocked_service_configuration(self):
        """Validate wiremock service."""
        logging.info('Validating mocked service fail to find `test` endpoint')
        mocked_service_response = requests.post('http://mocked.service:9999/test')
        self.assertEquals(mocked_service_response.status_code, httplib.NOT_FOUND)

        logging.info('Use WiremockController to stub the service `test` endpoint')
        stubs_dir_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'wiremock_stubs')
        dtt.WiremockController(url=self.MOCKED_SERVICE_URL).set_mapping_from_dir(stubs_dir_path)

        logging.info('Validating mocked service response on `test` endpoint')
        mocked_service_response = requests.post('http://mocked.service:9999/test')
        self.assertEquals(mocked_service_response.status_code, httplib.OK)

```

## Integrating With `nose2`
---
### Run the tests
```
$ CONFIG=test.cfg nose2 --config=test.cfg --verbose --project-directory .
```
Outcome:
```
test_mocked_service_configuration (tests.nose2_example.test_example.ExampleTest)
Validate wiremock service. ... ok
test_service_down (tests.nose2_example.test_example.ExampleTest)
Validate service down scenario. ... ok
test_services_sanity (tests.nose2_example.test_example.ExampleTest)
Validate services are responsive once the test context start. ... ok

----------------------------------------------------------------------
Ran 3 tests in 17.006s

OK

```

## Integrating With `pytest`
---
### Define a conftest.py File Describing The Required Fixture

```python
"""utilized by in pytest configuration."""
import os

import pytest

from docker_test_tools import config, environment

config = config.Config(config_path=os.environ.get('CONFIG', None))
controller = environment.EnvironmentController(log_path=config.log_path,
                                               project_name=config.project_name,
                                               compose_path=config.docker_compose_path,
                                               reuse_containers=config.reuse_containers)


@pytest.fixture(scope="session", autouse=True)
def global_setup_teardown():
    """This function will be executed once per testing session."""
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
platform linux2 -- Python 2.7.5, pytest-3.0.6, py-1.4.32, pluggy-0.4.0
rootdir: /home/sarbov/work/docker-test-tools, inifile: 
collected 3 items 

tests/pytest_example/test_example.py ...

==== ... ==== 3 passed in 16.89 seconds ==== ... ====
```
