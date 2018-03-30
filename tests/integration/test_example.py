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

    def test_mocked_service_request_journal(self):
        """Validate wiremock request journal."""
        log.info('Validating first request reaches the journal')
        requests.post(WIREMOCK_URL + '/some-unique-request-33452')
        journal = self.wiremock.get_request_journal()
        inner_url = journal[-1]['request']['url']
        self.assertEquals(inner_url, "/some-unique-request-33452")

        log.info('Validating filtering of specific requests from the journal')
        requests.post(WIREMOCK_URL + '/test2')
        requests.post(WIREMOCK_URL + '/test2')
        filtered = self.wiremock.get_matching_requests('/test2')
        self.assertEquals(len(filtered), 2)
        self.assertEquals(filtered[0]['request']['url'], "/test2")
        self.assertEquals(filtered[1]['request']['url'], "/test2")

        log.info('Validating the deletion of requests from the journal')
        self.wiremock.delete_request_journal()
        journal = self.wiremock.get_matching_requests('/test2')
        self.assertEquals(len(journal), 0)

        log.info('Validating stub ids are returned by mapping')
        stubs_dir_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'wiremock_stubs')
        stub_ids = self.wiremock.set_mapping_from_dir(stubs_dir_path)
        stub_file_path_example = os.path.join(stubs_dir_path, 'example.json')
        self.assertIn(stub_file_path_example, stub_ids)

        log.info('Validating filtering of specific requests from the journal by stub id')
        requests.post(WIREMOCK_URL + '/test')
        requests.post(WIREMOCK_URL + '/test')
        requests.post(WIREMOCK_URL + '/some-unique-request-33452')
        journal = self.wiremock.get_request_journal()
        self.assertEquals(len(journal), 3)
        filtered = self.wiremock.get_matching_requests(stub_id=stub_ids[stub_file_path_example])
        self.assertEquals(len(filtered), 2)
        self.assertEquals(filtered[0]['request']['url'], "/test")
        self.assertEquals(filtered[1]['request']['url'], "/test")
