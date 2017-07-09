import logging
from six.moves import http_client
import waiting
import requests

log = logging.getLogger(__name__)


def run_health_checks(checks, interval=1, timeout=60):
    """Return True if all health checks pass (return True).

    :param list checks: list of health check callables.
    :param int interval: interval (in seconds) between checks.
    :param int timeout: timeout (in seconds) for all checks to pass.

    :raise bool: True is all the services are healthy, False otherwise.
    """
    log.info('Waiting for the required health checks to pass...')
    try:
        waiting.wait(lambda: all([health_check() for health_check in checks]),
                     sleep_seconds=interval, timeout_seconds=timeout)

        return True

    except waiting.TimeoutExpired:
        log.error("Required health checks didn't pass within timeout")
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
    log.debug('Defining a CURL based health check for service: %s at: %s', service_name, url)

    def url_health_check():
        """Return True if the service is responsive."""
        is_ready = is_responsive(url, expected_status)
        log.debug('Service %s ready: %s', service_name, is_ready)
        return is_ready

    return url_health_check


# For backward compatability
get_curl_health_check = get_health_check