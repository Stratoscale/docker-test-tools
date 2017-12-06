import mock
import unittest

from docker_test_tools import utils


class TestUtils(unittest.TestCase):
    @mock.patch('requests.get')
    def test_run_health_checks(self, get_mock):
        """Validate the run_health_checks function."""
        get_mock.return_value = mock.MagicMock(status_code=200)
        utils.run_health_checks([utils.get_health_check('service1', 'first_url'),
                                 utils.get_health_check('service2', 'second_url')],
                                timeout=0)

        get_mock.assert_any_call('first_url', timeout=5)
        get_mock.assert_any_call('second_url', timeout=5)

        self.assertTrue(utils.run_health_checks([lambda: True, lambda: True], timeout=0))
        self.assertFalse(utils.run_health_checks([lambda: True, lambda: False], timeout=0))
        self.assertFalse(utils.run_health_checks([lambda: False, lambda: False], timeout=0))
