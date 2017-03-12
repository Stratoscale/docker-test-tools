import httplib
import logging
import requests

import docker_test_tools as dtt


class ExampleTest(dtt.BaseDockerTest):
    """Sanity test for docker-test-tools."""
    REQUIRED_HEALTH_CHECKS = [
        dtt.get_curl_health_check(service_name='redis.service', url='http://redis.service:6379'),
        dtt.get_curl_health_check(service_name='consul.service', url='http://consul.service:8500')
    ]

    def test_example(self):
        """Validate the docker-test-tools package."""
        logging.info('Validating consul container is responsive')
        consul_response = requests.get('http://consul.service:8500/v1/status/leader')
        self.assertEquals(consul_response.status_code, httplib.OK)

        consul_health_check = dtt.get_curl_health_check(service_name='consul.service', url='http://consul.service:8500')
        with self.controller.container_down(name='consul.service', health_check=consul_health_check):
            with self.assertRaises(requests.ConnectionError):
                requests.get('http://consul.service:8500/v1/status/leader')

        logging.info('Validating consul container is responsive')
        consul_response = requests.get('http://consul.service:8500/v1/status/leader')
        self.assertEquals(consul_response.status_code, httplib.OK)
