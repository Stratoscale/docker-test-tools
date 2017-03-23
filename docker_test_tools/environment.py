import logging
import subprocess

import config

import waiting
from contextlib import contextmanager


class EnvironmentController(object):
    """Utility for managing environment operations."""

    def __init__(self, project_name, compose_path, log_path, reuse_containers=False):
        self.log_path = log_path
        self.project_name = project_name
        self.compose_path = compose_path
        self.reuse_containers = reuse_containers

        self.services = self.get_services()

    @classmethod
    def from_file(cls, config_path):
        """Return an environment controller based on the given config.

        :return EnvironmentController: controller based on the given config
        """
        config_object = config.Config(config_path=config_path)
        return cls(log_path=config_object.log_path,
                   project_name=config_object.project_name,
                   compose_path=config_object.docker_compose_path,
                   reuse_containers=config_object.reuse_containers)

    def get_services(self):
        """Get the services info based on the compose file.

        :return dict: of format {'service-name': check_callback}
        """
        logging.debug("Getting environment services, using docker compose: %s", self.compose_path)
        try:
            services_output = subprocess.check_output(
                ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'config', '--services'],
                stderr=subprocess.STDOUT
            )

        except subprocess.CalledProcessError as error:
            raise RuntimeError("Failed getting environment services, reason: %s" % error.output)

        return services_output.strip().split('\n')

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
            raise RuntimeError("Failed running environment containers, reason: %s" % error.output)

    def kill_containers(self):
        """Kill the environment containers."""
        logging.debug("Killing environment containers, using docker compose: %s", self.compose_path)
        try:
            subprocess.check_output(
                ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'kill'],
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as error:
            raise RuntimeError("Failed killing environment containers, reason: %s" % error.output)

    def get_containers_logs(self):
        """Write the environment containers logs into a file."""
        logging.info("Writing containers logs to %s", self.log_path)
        try:
            subprocess.check_output(
                'docker-compose -f {compose_path} -p {project_name} logs --no-color > {log_path}'.format(
                    compose_path=self.compose_path, project_name=self.project_name,log_path=self.log_path),
                shell=True, stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as error:
            raise RuntimeError("Failed writing environment containers log, reason: %s" % error.output)

    def remove_containers(self):
        """Remove the environment containers."""
        logging.debug("Removing environment containers, using docker compose: %s", self.compose_path)
        try:
            subprocess.check_output(
                ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'rm', '-f'],
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as error:
            raise RuntimeError("Failed removing environment containers, reason: %s" % error.output)

    def kill_container(self, name):
        """Kill the container.

        :param str name: container name as it appears in the docker compose file.
        """
        self.validate_service_name(name)
        logging.debug("Killing %s container", name)
        try:
            subprocess.check_output(
                ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'kill', name],
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as error:
            raise RuntimeError("Failed killing container %s reason: %s" % (name, error.output))

    def restart_container(self, name):
        """Restart the container.

        :param str name: container name as it appears in the docker compose file.
        """
        self.validate_service_name(name)
        logging.debug("Restarting container %s", name)
        try:
            subprocess.check_output(
                ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'restart', name],
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as error:
            raise RuntimeError("Failed restarting container %s reason: %s" % (name, error.output))

    def get_container_id(self, name):
        """Get container id by name.

        :param str name: container name as it appears in the docker compose file.
        """
        self.validate_service_name(name)
        try:
            return subprocess.check_output(
                ['docker-compose', '-f', self.compose_path, '-p', self.project_name, 'ps', '-q', name],
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as error:
            raise RuntimeError("Failed getting container %s id, reason: %s" % (name, error.output))

    def is_container_ready(self, name):
        """"Return True if the container is in ready state.

        If a health check is defined, a healthy container will be considered as ready.
        If no health check is defined, a running container will be considered as ready.

        :param str name: container name as it appears in the docker compose file.
        """
        self.validate_service_name(name)
        logging.debug("Getting %s container state", name)
        container_id = self.get_container_id(name)
        try:
            status_output = subprocess.check_output(r"docker inspect --format='{{json .State}}' " + container_id,
                                             shell=True)

        except subprocess.CalledProcessError as error:
            logging.warning("Failed getting container %s state, reason: %s", name, error.output)
            return False

        if '"Health":' in status_output:
            is_ready = '"Status":"healthy"' in status_output
        else:
            is_ready = '"Status":"running"' in status_output

        logging.debug("Container %s ready: %s", name, is_ready)
        return is_ready

    def wait_for_services(self, services=None, interval=1, timeout=60):
        """Wait for the services checks to pass.

        If the service compose configuration contains an health check, the method will wait for a 'healthy' state.
        If it doesn't the method will wait for a 'running' state.
        """
        services = services if services else self.services
        logging.info('Waiting for %s to reach the required state', services)

        def service_checks():
            """Return True if services checks pass."""
            return all([self.is_container_ready(name) for name in services])

        try:
            waiting.wait(service_checks, sleep_seconds=interval, timeout_seconds=timeout)
            logging.info('Services %s reached the required state', services)
            return True

        except waiting.TimeoutExpired:
            logging.error('%s failed to to reach the required state', services)
            return False

    @contextmanager
    def container_down(self, name, interval=1, timeout=60):
        """Container down context manager.

        Simulate container down scenario by killing the container within the context,
        once context ends restart the container and wait for the service check to pass.

        :param str name: container name as it appears in the docker compose file.
        :param int interval: interval (in seconds) between checks.
        :param int timeout: timeout (in seconds) for all checks to pass.

        Usage:

        >>> with controller.service_down(name='consul'):
        >>>     # container will be down in this context
        >>>
        >>> # container will be back up after context end
        """
        self.validate_service_name(name)
        self.kill_container(name=name)
        try:
            yield
        finally:
            self.restart_container(name=name)
            self.wait_for_services(services=[name, ], interval=interval, timeout=timeout)

    def validate_service_name(self, name):
        if name not in self.services:
            raise ValueError('Invalid service name: %r, must be one of %s' % (name, self.services))
