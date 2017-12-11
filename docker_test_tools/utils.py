import logging

import waiting
import requests

from six.moves import http_client
from multiprocessing.pool import ThreadPool

log = logging.getLogger(__name__)


def run_health_checks(checks, interval=1, timeout=60):
    """Return True if all health checks pass (return True).

    :param list checks: list of health check callables.
    :param int interval: interval (in seconds) between checks.
    :param int timeout: timeout (in seconds) for all checks to pass.

    :raise bool: True is all the services are healthy, False otherwise.
    """
    pool = ThreadPool()
    async_results = [pool.apply_async(wait_for_health, (check, interval, timeout)) for check in checks]
    return all([async_result.get() for async_result in async_results])


def wait_for_health(health_check, interval=1, timeout=60):
    try:
        return waiting.wait(health_check, sleep_seconds=interval, timeout_seconds=timeout)
    except waiting.TimeoutExpired:
        return False


def is_responsive(address, expected_status=http_client.OK):
    """Return True if the address is responsive.

    :param string address: url address 'hostname:port'.
    :param int expected_status: expected response status code.
    :return bool: True is the address is responsive, False otherwise.
    """
    try:
        return requests.get(address, timeout=5).status_code == expected_status
    except:
        return False


def get_health_check(service_name, url, expected_status=http_client.OK):
    """Return a function used to determine if the given service is responsive.

    :param string service_name: service name.
    :param string url: service url 'hostname:port'.
    :param int expected_status: expected response status code.

    :return function: function used to determine if the given service is responsive.
    """
    log.debug('Defining a health check for service: %s at: %s', service_name, url)

    def url_health_check():
        """Return True if the service is responsive."""
        is_ready = is_responsive(url, expected_status)
        log.debug('Service %s ready: %s', service_name, is_ready)
        return is_ready

    return url_health_check


def to_str(value):
    """Return the value as string.

    For python3 compatibility
    """
    if isinstance(value, str):
        return value

    if isinstance(value, bytes):
        return value.decode('utf-8')

    raise Exception("Type {} was not converted to string".format(type(value)))


# For backward compatibility
get_curl_health_check = get_health_check
