import mock
from six.moves import http_client
import unittest

from docker_test_tools import wiremock


class TestWiremockController(unittest.TestCase):

    def setUp(self):
        self.controller = wiremock.WiremockController(url='http://mocked.service:9999')
        with open("tests/resources/ut/requests-journal.json") as journal_file:
            self.journal_json = journal_file.read()

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
            mock_response.json.return_value = {'uuid': '162d458b-86d6-4161-9918-02cf27566422'}
            # Setting mapping should pass
            stub_id = self.controller.set_mapping_from_json(test_json)
            mock_post.assert_any_call('http://mocked.service:9999/__admin/mappings', json=test_json)
            self.assertEqual(stub_id, '162d458b-86d6-4161-9918-02cf27566422')

    @mock.patch('docker_test_tools.wiremock.WiremockController.set_mapping_from_json')
    def test_set_mapping_from_file(self, from_json_mock):
        """Test 'set_mapping_from_file' method."""
        # Define mock target name for 'open'
        open_name = '%s.open' % wiremock.__name__
        from_json_mock.return_value = '162d458b-86d6-4161-9918-02cf27566422'

        # Mock open & file object to return a valid json when read
        m = mock.mock_open(read_data='{"valid": "json"}')
        with mock.patch(open_name, m, create=True):
            stub_id = self.controller.set_mapping_from_file('json-file-path')
            from_json_mock.assert_called_once_with({u"valid": u"json"})
            self.assertEqual(stub_id, '162d458b-86d6-4161-9918-02cf27566422')

    @mock.patch('docker_test_tools.wiremock.WiremockController.set_mapping_from_file')
    def test_set_mapping_from_files(self, from_file_mock):
        """Test 'set_mapping_from_files' method."""
        test_paths = ['json-file-path-1', 'json-file-path-2']
        stub_ids = ['162d458b-86d6-4161-9918-02cf27566422', '41a0a68b-ecf3-4879-9542-a12028bd7c09']
        from_file_mock.side_effect = stub_ids

        stub_id_dict = self.controller.set_mapping_from_files(test_paths)
        for test_path in test_paths:
            from_file_mock.assert_any_call(test_path)

        self.assertDictEqual(stub_id_dict, dict(zip(test_paths, stub_ids)))

    @mock.patch('os.path.isdir')
    @mock.patch('docker_test_tools.wiremock.WiremockController.set_mapping_from_files')
    def test_set_mapping_from_dir(self, from_files_mock, is_dir_mock):
        """Test 'set_mapping_from_dir' method."""
        test_paths = ['json-file-path-1', 'json-file-path-2']
        test_dir = 'some/dir'
        is_dir_mock.return_value = True

        with mock.patch('glob.iglob') as glob_mock:
            glob_mock.return_value = test_paths
            self.controller.set_mapping_from_dir(test_dir)
            glob_mock.assert_called_once_with('some/dir/*.json')
            from_files_mock.assert_called_once_with(test_paths)

    def test_get_request_journal(self):
        """Test 'get_request_journal' method."""

        mock_response = mock.Mock()
        mock_response.status_code = http_client.OK
        mock_response.text = self.journal_json
        mock_get = mock.Mock(return_value=mock_response)

        with mock.patch("requests.get", mock_get):
            requests = self.controller.get_request_journal()
            mock_get.assert_called_once_with("http://mocked.service:9999/__admin/requests")
            self.assertEquals(requests[0]["request"]["url"], "/received-request/7")
            self.assertEquals(requests[1]["request"]["url"], "/received-request/6")

    def test_error_getting_request_journal(self):
        """Test HTTP error while getting request journal."""

        mock_response = mock.Mock()
        mock_response.status_code = http_client.NOT_FOUND
        mock_get = mock.Mock(return_value=mock_response)

        with mock.patch("requests.get", mock_get):
            self.assertRaises(ValueError, self.controller.get_request_journal)

    def test_get_matching_requests(self):
        """Test 'get_matching_requests' method."""

        mock_response = mock.Mock()
        mock_response.status_code = http_client.OK
        mock_response.text = self.journal_json
        mock_get = mock.Mock(return_value=mock_response)

        with mock.patch("requests.get", mock_get):
            requests = self.controller.get_matching_requests("/received-request/6")
            mock_get.assert_called_once_with("http://mocked.service:9999/__admin/requests")
            self.assertEquals(len(requests), 1)
            self.assertEquals(requests[0]["request"]["url"], "/received-request/6")

            mock_get.reset_mock()
            requests = self.controller.get_matching_requests(stub_id="162d458b-86d6-4161-9918-02cf27566422")
            mock_get.assert_called_once_with("http://mocked.service:9999/__admin/requests")
            self.assertEquals(len(requests), 1)
            self.assertEquals(requests[0]["stubMapping"]["uuid"], "162d458b-86d6-4161-9918-02cf27566422")

    def test_delete_request_journal(self):
        """Test 'delete_request_journal' method."""

        mock_delete = mock.Mock()

        with mock.patch("requests.delete", mock_delete):
            self.controller.delete_request_journal()
            mock_delete.assert_called_once_with("http://mocked.service:9999/__admin/requests")

    def test_set_mapping_from_non_existing_dir(self):
        """Test 'set_mapping_from_non_existing_dir' method."""
        test_paths = ['json-file-path-1', 'json-file-path-2']
        test_dir = 'some/dir'

        with self.assertRaises(ValueError):
            self.controller.set_mapping_from_dir(test_dir)
