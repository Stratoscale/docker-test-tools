import mock
import unittest

from waiting import TimeoutExpired
from docker_test_tools import utils


class TestUtils(unittest.TestCase):
    @mock.patch('requests.get')
    def test_run_health_checks(self, get_mock):
        """Validate the run_health_checks function."""
        get_mock.return_value = mock.MagicMock(status_code=200)
        utils.run_health_checks([utils.get_curl_health_check('service1', 'first_url'),
                                 utils.get_curl_health_check('service2', 'second_url')],
                                timeout=5)

        get_mock.assert_any_call('first_url', timeout=5)
        get_mock.assert_any_call('second_url', timeout=5)

        with mock.patch("waiting.wait", return_value=True):
            self.assertTrue(utils.run_health_checks([]))

        with mock.patch("waiting.wait", side_effect=TimeoutExpired(timeout_seconds=1, what='something')):
            self.assertFalse(utils.run_health_checks([]))


