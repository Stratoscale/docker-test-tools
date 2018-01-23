"""Utility for managing wiremock based services.

For more info about wiremock visit: http://wiremock.org
"""
import os
import json
import glob
from six.moves import http_client
import logging

import requests

log = logging.getLogger(__name__)


class WiremockError(Exception):
    """Raised on wiremock controller failures."""
    pass


class WiremockController(object):
    """Utility for managing wiremock based services.

    Usage example:

    >>> controller = WiremockController(url='http://test.service:9999')
    >>> controller.set_mapping_from_dir('some/config/dir')
    >>> controller.reset_mapping()
    """

    def __init__(self, url):
        """Initialize the wiremock controller.

        :param str url: wiremock service url.
        """
        self.url = url
        self.admin_url = os.path.join(url, "__admin")
        self.admin_mapping_url = os.path.join(self.admin_url, "mappings")
        self.mapping_reset_url = os.path.join(self.admin_mapping_url, 'reset')
        self.requests_url = "%s/requests" % self.admin_url

    def set_mapping_from_dir(self, dir_path):
        """Set wiremock service mapping based on given directory.

        :param str dir_path: directory path to scan - should contain json mapping files.
        :return dict: of format {json_file_path: stub_uuid} the uuid of the mapping stub
        """
        log.debug('Setting service %s wiremock mapping using directory %s', self.url, dir_path)
        if not os.path.isdir(dir_path):
            raise ValueError("'%s' is not a valid dir" % dir_path)

        mapping_files_pattern = os.path.join(dir_path, '*.json')
        return self.set_mapping_from_files(glob.iglob(mapping_files_pattern))

    def set_mapping_from_files(self, json_paths):
        """Set wiremock service mapping based on given json paths.

        :param list json_paths: list of json stub file paths.
        :return dict: of format {json_file_path: stub_uuid} the uuid of the mapping stub
        """

        return {json_path: self.set_mapping_from_file(json_path) for json_path in json_paths}

    def set_mapping_from_file(self, json_path):
        """Set wiremock service mapping based on given json path.

        :param str json_path: json stub file path.
        :return str: the uuid of the mapping stub
        """
        log.debug('Setting service %s wiremock mapping using file %s', self.url, json_path)
        with open(json_path, 'r') as json_file:
            json_object = json.load(json_file)
        return self.set_mapping_from_json(json_object)

    def set_mapping_from_json(self, json_object):
        """Set wiremock service mapping based on given json object.

        :param json_object: json data of mapping stub.
        :return str: the uuid of the mapping stub
        :raise WiremockError: on failure to configure service.
        """
        log.debug('Setting service %s wiremock mapping using json: %s', self.url, json_object)
        try:
            resp = requests.post(self.admin_mapping_url, json=json_object)
            resp.raise_for_status()
        except:
            log.exception("Failed setting service %s wiremock mapping using json: %s", self.url, json_object)
            raise WiremockError("Failed setting service %s wiremock mapping using json: %s" % (self.url, json_object))

        return resp.json()['uuid']

    def reset_mapping(self):
        """Reset wiremock service mapping.

        :raise WiremockError: on failure to reset service mapping.
        """
        log.debug('Resetting %s wiremock mapping', self.url)
        try:
            requests.post(self.mapping_reset_url).raise_for_status()
        except:
            log.exception('Failed resetting %s wiremock mapping', self.url)
            raise WiremockError('Failed resetting %s wiremock mapping' % self.url)

    def get_request_journal(self):
        """Get the wiremock service request journal.

        :raise ValueError: on failure to retrieve journal from Wiremock admin API.
        """
        response = requests.get(self.requests_url)
        if response.status_code != http_client.OK:
            raise ValueError(response.text, response.status_code)
        response_body = json.loads(response.text)
        return response_body["requests"]

    def get_matching_requests(self, inner_url=None, stub_id=None):
        """Get all wiremock service requests of the given type (by inner URL) from  the journal.

        :param inner_url: The inner URL with which to filter journal requests by matching.
        :param stub_id: The matched stub id with which to filter journal requests by matching.
        """
        matching_requests = []
        for request in self.get_request_journal():
            if inner_url is not None and request["request"]["url"] != inner_url:
                continue
            if stub_id is not None and (not request["wasMatched"] or request["stubMapping"]["uuid"] != stub_id):
                continue
            matching_requests.append(request)

        return matching_requests

    def delete_request_journal(self):
        """Delete all entries from the service request journal."""
        requests.delete(self.requests_url).raise_for_status()
