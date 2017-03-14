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
