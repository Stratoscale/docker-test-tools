import mock
import unittest

from docker_test_tools import wiremock


class TestWiremockController(unittest.TestCase):

    def setUp(self):
        self.controller = wiremock.WiremockController(url='http://mocked.service:9999')

    def test_reset_mapping(self):
        """Test reset mapping method."""
        # Reset should fail - service url is not reachable
        with self.assertRaises(wiremock.WiremockError):
            self.controller.reset_mapping()

        # Mock requests objects
        mock_response = mock.MagicMock()
        mock_post = mock.MagicMock(return_value=mock_response)

        with mock.patch("requests.post", mock_post):

            # Mock response assertion to fail
            mock_response.raise_for_status = mock.MagicMock(side_effect=Exception("requests-failure"))

            # Reset should fail - bad response
            with self.assertRaises(wiremock.WiremockError):
                self.controller.reset_mapping()

            # Mock response assertion to pass
            mock_response.raise_for_status = mock.MagicMock()

            # Reset should pass
            self.controller.reset_mapping()
            mock_post.assert_any_call('http://mocked.service:9999/__admin/mappings/reset')

    def test_set_mapping_from_json(self):
        """Test 'set_mapping_from_json' method."""
        test_json = {u"valid": u"json"}

        # Setting mapping should fail - service url is not reachable
        with self.assertRaises(wiremock.WiremockError):
            self.controller.set_mapping_from_json(test_json)

        # Mock requests objects
        mock_response = mock.MagicMock()
        mock_post = mock.MagicMock(return_value=mock_response)

        with mock.patch("requests.post", mock_post):

            # Mock response assertion to fail
            mock_response.raise_for_status = mock.MagicMock(side_effect=Exception("requests-failure"))

            # Setting mapping should fail - bad response
            with self.assertRaises(wiremock.WiremockError):
                self.controller.set_mapping_from_json(test_json)

            # Mock response assertion to pass
            mock_response.raise_for_status = mock.MagicMock()

            # Setting mapping should pass
            self.controller.set_mapping_from_json(test_json)
            mock_post.assert_any_call('http://mocked.service:9999/__admin/mappings', json=test_json)

    @mock.patch('docker_test_tools.wiremock.WiremockController.set_mapping_from_json')
    def test_set_mapping_from_file(self, from_json_mock):
        """Test 'set_mapping_from_file' method."""
        # Define mock target name for 'open'
        open_name = '%s.open' % wiremock.__name__

        # Mock open & file object to return a valid json when read
        m = mock.mock_open(read_data='{"valid": "json"}')
        with mock.patch(open_name, m, create=True):
            self.controller.set_mapping_from_file('json-file-path')
            from_json_mock.assert_called_once_with({u"valid": u"json"})

    @mock.patch('docker_test_tools.wiremock.WiremockController.set_mapping_from_file')
    def test_set_mapping_from_files(self, from_file_mock):
        """Test 'set_mapping_from_files' method."""
        test_paths = ['json-file-path-1', 'json-file-path-2']
        self.controller.set_mapping_from_files(test_paths)
        for test_path in test_paths:
            from_file_mock.assert_any_call(test_path)

    @mock.patch('docker_test_tools.wiremock.WiremockController.set_mapping_from_files')
    def test_set_mapping_from_dir(self, from_files_mock):
        """Test 'set_mapping_from_dir' method."""
        test_paths = ['json-file-path-1', 'json-file-path-2']
        test_dir = 'some/dir'

        with mock.patch('glob.iglob') as glob_mock:
            glob_mock.return_value = test_paths
            self.controller.set_mapping_from_dir(test_dir)
            glob_mock.assert_called_once_with('some/dir/*.json')
            from_files_mock.assert_called_once_with(test_paths)
