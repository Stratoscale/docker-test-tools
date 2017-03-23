import logging
import subprocess
import os.path
from contextlib import contextmanager

import utils


class EnvironmentController(object):
    """Utility for managing environment operations."""

    def __init__(self, project_name, compose_path, log_path, reuse_containers=False):
        self.log_path = log_path
        self.project_name = project_name
        self.compose_path = compose_path
        self.reuse_containers = reuse_containers

    def setup(self):
        """Sets up the environment using docker commands.

        Should be called once before *all* the tests start.
        """
        try:
            logging.debug("Setting up the environment")
            self.cleanup()
            self.run_containers()
        except:
            logging.exception("Setup failure, tearing down the test environment")
            self.teardown()
            raise

    def teardown(self):
        """Tears down the environment using docker commands.

        Should be called once after *all* the tests finish.
        """
        logging.debug("Tearing down the environment")
        try:
            self.get_containers_logs()
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup the environment.

        Kills and removes the environment containers.
        """
        if self.reuse_containers:
            logging.warning("Container reuse enabled: Skipping environment cleanup")
            return

        self.kill_containers()
        self.remove_containers()

    def run_containers(self):
        """Run environment containers."""
        logging.debug("Running environment containers, using docker compose: %s", self.compose_path)
        try:
            subprocess.check_output(
                ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'up', '--build', '-d'],
                stderr=subprocess.STDOUT
            )

        except subprocess.CalledProcessError as error:
            raise RuntimeError("Failed running environment containers, reason: \n%s", error.output)

    def kill_containers(self):
        """Kill the environment containers."""
        logging.debug("Killing environment containers, using docker compose: %s", self.compose_path)
        try:
            subprocess.check_output(
                ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'kill'],
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as error:
            raise RuntimeError("Failed killing environment containers, reason: \n%s", error.output)

    def _get_service_list(self):
        try:
            text = subprocess.check_output('docker-compose -f {compose_path} config --services'.format(compose_path=self.compose_path),
                                           shell=True, stderr=subprocess.STDOUT)

        except subprocess.CalledProcessError as error:
            raise RuntimeError("Failed getting list of services, reason: \n%s", error.output)
        return text.strip().split('\n')

    def _service_log_file_name(self, service_name=None):
        if not service_name:
            return self.log_path
        log_dir, _ = os.path.split(self.log_path)
        return os.path.join(log_dir, '{}.log'.format(service_name))

    def _get_container_logs(self, service_name=None):
        """Write the logs of a service container (or all of them) to files."""
        log_path = self._service_log_file_name(service_name)
        logging.info("Writing containers logs to %s, using docker compose: %s", log_path, self.compose_path)
        try:
            subprocess.check_output(
                'docker-compose -f {compose_path} -p {project_name} logs --no-color {service_name} > {log_path}'.format(
                    compose_path=self.compose_path, project_name=self.project_name, log_path=log_path,
                    service_name=service_name or ''),
                shell=True, stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as error:
            raise RuntimeError("Failed writing environment containers log, reason: \n%s", error.output)

    def _find_unmatched_requests(self, service_names):
        unmatched_requests = []
        for service_name in service_names:
            if not service_name:
                continue
            log_path = self._service_log_file_name(service_name)
            found = False
            wiremock_initiated = False
            for line in open(log_path):
                if 'Received request to /mappings with body' in line:
                    wiremock_initiated = True
                if not wiremock_initiated:
                    continue
                if 'Request was not matched:' in line:
                    unmatched_requests.append([service_name, '?', '?'])
                    found = True
                if found:
                    tokens = line.split()
                    if tokens[2] == '"absoluteUrl"':
                        unmatched_requests[-1][2] = tokens[4][1:-2]
                    if tokens[2] == '"method"':
                        unmatched_requests[-1][1] = tokens[4][1:-2]
                        found = False

        log_dir, _ = os.path.split(self.log_path)
        filename = os.path.join(log_dir, 'unmatched_requests')
        with open(filename, 'w') as out:
            for request in unmatched_requests:
                out.write('{}\n'.format('\t'.join(request)))

    def get_containers_logs(self):
        self._get_container_logs()
        service_names = self._get_service_list() + [None]
        for service_name in service_names:
            self._get_container_logs(service_name)
        self._find_unmatched_requests(service_names)

    def remove_containers(self):
        """Remove the environment containers."""
        logging.debug("Removing environment containers, using docker compose: %s", self.compose_path)
        try:
            subprocess.check_output(
                ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'rm', '-f'],
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as error:
            raise RuntimeError("Failed removing environment containers, reason: \n%s", error.output)

    def kill_container(self, name):
        """Kill the container.

        :param str name: container name as it appears in the docker compose file.
        """
        logging.debug("Killing container %s, using docker compose: %s", name, self.compose_path)
        try:
            subprocess.check_output(
                ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'kill', name],
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as error:
            raise RuntimeError("Failed killing container %s  reason: \n%s", name, error.output)

    def restart_container(self, name):
        """Restart the container.

        :param str name: container name as it appears in the docker compose file.
        """
        logging.debug("Restarting container %s, using docker compose: %s", name, self.compose_path)
        try:
            subprocess.check_output(
                ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'restart', name],
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as error:
            raise RuntimeError("Failed restarting container %s  reason: \n%s", name, error.output)

    @contextmanager
    def container_down(self, name, health_check, interval=1, timeout=60):
        """Container down context manager.

        Simulate container down scenario by killing the container within the context,
        once context ends restart the container and wait for the health check to pass.

        :param str name: container name as it appears in the docker compose file.
        :param callable health_check: callable used to verify the container health.
        :param int interval: interval (in seconds) between checks.
        :param int timeout: timeout (in seconds) for all checks to pass.

        Usage:

        >>> health_check = utils.get_curl_health_check(service_name='consul', url='http://consul.service:8500')
        >>>
        >>> with controller.service_down(service_name='consul', health_check=health_check):
        >>>     # container will be down in this context
        >>>
        >>> # container will be back up after context end
        """
        self.kill_container(name=name)
        try:
            yield
        finally:
            self.restart_container(name=name)
            utils.run_health_checks(checks=[health_check, ], interval=interval, timeout=timeout)
