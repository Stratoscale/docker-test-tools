import mock
import unittest
import subprocess

from docker_test_tools import utils


class TestUtils(unittest.TestCase):

    @mock.patch('subprocess.call')
    def test_run_health_checks(self, call_mock):
        """Validate the are_services_ready method."""
        call_mock.return_value = 0
        utils.run_health_checks([utils.get_curl_health_check('service1', 'first_url'),
                                 utils.get_curl_health_check('service2', 'second_url')])

        call_mock.assert_any_call(['curl', '-s', 'first_url'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        call_mock.assert_any_call(['curl', '-s', 'second_url'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
