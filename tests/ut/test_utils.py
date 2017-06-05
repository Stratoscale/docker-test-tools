import mock
import unittest
import subprocess

from waiting import TimeoutExpired
from docker_test_tools import utils


class TestUtils(unittest.TestCase):
    @mock.patch('subprocess.call')
    def test_run_health_checks(self, call_mock):
        """Validate the run_health_checks function."""
        call_mock.return_value = 0
        utils.run_health_checks([utils.get_curl_health_check('service1', 'first_url'),
                                 utils.get_curl_health_check('service2', 'second_url')])

        call_mock.assert_any_call(['curl', '-s', 'first_url'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        call_mock.assert_any_call(['curl', '-s', 'second_url'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        with mock.patch("waiting.wait", return_value=True):
            self.assertTrue(utils.run_health_checks([]))

        with mock.patch("waiting.wait", side_effect=TimeoutExpired(timeout_seconds=1, what='something')):
            self.assertFalse(utils.run_health_checks([]))


