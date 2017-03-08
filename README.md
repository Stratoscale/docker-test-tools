# Docker Test Tools
The `docker-test-tools` package makes it easy to write tests that relies on docker containers enviorement in order to operate.

#### Prerequisites
* The project under test must be [skipper](https://github.com/Stratoscale/skipper) compatible 

#### Features
* Manage container operation easly within the tests.
* Setup and tear down containers environment as part of the tests run flow.
* Integrated with [nose2](https://nose2.readthedocs.io/en/latest/index.html) and [pytest](http://doc.pytest.org/en/latest/) test runners.


## Setup

### Define a docker compose file describing the required test environment

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

  redis.service:
    image: redis:alpine
    networks: [tests-network]


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

### Define tests based on `DockerBaseTest`

For example: `test_example.py`
```python
import httplib
import logging
import requests

import docker_test_tools as dtt


class ExampleTest(dtt.BaseDockerTest):
    """Sanity test for docker-test-tools."""
    REQUIRED_HEALTH_CHECKS = [
        dtt.get_curl_health_check(service_name='redis', url='http://redis.service:6379'),
        dtt.get_curl_health_check(service_name='consul', url='http://consul.service:8500')
    ]

    def test_example(self):
        """Validate the docker-test-tools package."""
        logging.info('Validating consul container is responsive')
        response = requests.get('http://consul.service:8500/v1/status/leader')
        self.assertEquals(response.status_code, httplib.OK)
```

## Integrating With `nose2`
---
### Run the tests
```
$ CONFIG=test.cfg nose2 --config=test.cfg --verbose --project-directory .
```
Outcome:
```
test_example (tests.example.test_example.ExampleTest)
Validate the docker-test-tools package. ... ok

----------------------------------------------------------------------
Ran 1 test in 9.535s

OK
```

## Integrating With `pytest`
---
### Define a conftest.py file describing the required fixture

```python
"""utilized by in pytest configuration."""
import pytest

from docker_test_tools.layer import EnvironmentLayer


@pytest.fixture(scope="session", autouse=True)
def global_setup_teardown():
    """This function will be executed once per testing session."""
    EnvironmentLayer.setUp()
    yield
    EnvironmentLayer.tearDown()
```

### Run the tests
```
$ CONFIG=tests/pytest_example/test.cfg pytest tests/pytest_example/
```

Outcome:
```
===== ... ==== test session starts ==== ... ====
platform linux2 -- Python 2.7.5, pytest-3.0.6, py-1.4.32, pluggy-0.4.0
...
collected 1 items 

tests/pytest_example/test_example.py .

===== ... ==== 1 passed in 9.78 seconds ==== ... ====


```
