import os
import httplib
import logging
import requests

from docker_test_tools.base_test import BaseDockerTest
from docker_test_tools.wiremock import WiremockController


class ExampleTest(BaseDockerTest):
    """Usage example test for docker-test-tools."""
    # Services names as they appear in the docker-compose.yml
    CONSUL_SERVICE_NAME = 'consul.service'
    MOCKED_SERVICE_NAME = 'mocked.service'

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
        with self.controller.container_down(name=self.CONSUL_SERVICE_NAME):
            with self.assertRaises(requests.ConnectionError):
                requests.get('http://consul.service:8500')

        logging.info('Validating consul container has recovered and is responsive')
        self.assertEquals(requests.get('http://consul.service:8500').status_code, httplib.OK)

    def test_mocked_service_configuration(self):
        """Validate wiremock service."""
        logging.info('Validating mocked service fail to find `test` endpoint')
        self.assertEquals(requests.post('http://mocked.service:9999/test').status_code, httplib.NOT_FOUND)

        logging.info('Use WiremockController to stub the service `test` endpoint')
        stubs_dir_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'wiremock_stubs')
        WiremockController(url='http://mocked.service:9999').set_mapping_from_dir(stubs_dir_path)

        logging.info('Validating mocked service response on `test` endpoint')
        self.assertEquals(requests.post('http://mocked.service:9999/test').status_code, httplib.OK)
