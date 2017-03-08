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
