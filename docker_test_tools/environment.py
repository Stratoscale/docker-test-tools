import logging
import os
from contextlib import contextmanager
from functools import partial

import docker
import waiting

from docker_test_tools import config
from docker_test_tools import logs
from docker_test_tools import stats
from docker_test_tools import utils
from docker_test_tools.api_version import get_server_api_version
from docker_test_tools.compose import Compose

log = logging.getLogger(__name__)


class EnvironmentController(object):
    """Utility for managing environment operations."""

    def __init__(
        self,
        project_name,
        compose_path,
        compose_command,
        log_path,
        collect_stats=False,
        reuse_containers=False,
    ):
        self.log_path = log_path
        self.compose_path = compose_path
        self.project_name = project_name
        self.reuse_containers = reuse_containers

        self.docker_client = docker.client.APIClient()
        self.environment_variables = self._get_environment_variables()
        self.compose = Compose(
            compose_path=compose_path,
            project_name=project_name,
            environment_variables=self.environment_variables,
            command=compose_command,
        )

        self.services = self.get_services()
        self.encoding = self.environment_variables.get("PYTHONIOENCODING", "utf-8")
        self.work_dir = os.path.dirname(self.log_path)
        self.logs_collector = logs.LogCollector(
            log_path=log_path,
            encoding=self.encoding,
            compose=self.compose,
        )

        self.plugins = []
        self.plugins.append(self.logs_collector)

        if collect_stats:
            self.plugins.append(
                stats.StatsCollector(
                    encoding=self.encoding,
                    project=self.project_name,
                    target_dir_path=self.work_dir,
                    environment_variables=self.environment_variables,
                )
            )

    @classmethod
    def from_file(cls, config_path):
        """Return an environment controller based on the given config.

        :return EnvironmentController: controller based on the given config
        """
        config_object = config.Config(config_path=config_path)
        return cls(
            log_path=config_object.log_path,
            project_name=config_object.project_name,
            collect_stats=config_object.collect_stats,
            compose_path=config_object.docker_compose_path,
            compose_command=config_object.docker_compose_command,
            reuse_containers=config_object.reuse_containers,
        )

    def get_services(self):
        """Get the services info based on the compose file.

        :return list: service names.
        """
        log.debug(
            "Getting environment services, using docker compose: %s", self.compose_path
        )

        return self.compose.get_services()

    def setup(self):
        """Sets up the environment using docker commands.

        Should be called once before *all* the tests start.
        """
        try:
            log.debug("Setting up the environment")
            self.cleanup()
            self.up()

            for plugin in self.plugins:
                try:
                    plugin.start()
                except:
                    logging.warning("Failed starting Plugin %s, skipping", plugin)

        except:
            log.exception("Setup failure, tearing down the test environment")
            self.teardown()
            raise

    def teardown(self):
        """Tears down the environment using docker commands.

        Should be called once after *all* the tests finish.
        """
        log.debug("Tearing down the environment")
        try:
            for plugin in self.plugins:
                try:
                    plugin.stop()
                except:
                    logging.warning("Failed stopping Plugin %s, skipping", plugin)
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup the environment.

        Kills and removes the environment containers.
        """
        if self.reuse_containers:
            log.warning("Container reuse enabled: Skipping environment cleanup")
            return

        self.down()

    def up(self):
        """Run environment containers."""
        log.debug("Setting environment up, using docker compose: %s", self.compose_path)
        self.compose.up()

    def down(self):
        """Stop and remove environment containers."""
        log.debug(
            "Taking environment down, using docker compose: %s", self.compose_path
        )
        self.compose.down()

    def kill_container(self, name):
        """Kill the container.

        :param str name: container name as it appears in the docker compose file.
        """
        log.debug("Killing %s container", name)
        container_id = self.get_container_id(name=name)
        self.docker_client.kill(container_id)

    def restart_container(self, name):
        """Restart the container.

        :param str name: container name as it appears in the docker compose file.
        """
        log.debug("Restarting %s container", name)
        container_id = self.get_container_id(name=name)
        self.docker_client.restart(container_id)

    def pause_container(self, name):
        """Pause the container.

        :param str name: container name as it appears in the docker compose file.
        """
        log.debug("Pausing %s container", name)
        container_id = self.get_container_id(name=name)
        self.docker_client.pause(container_id)

    def unpause_container(self, name):
        """Unpause the container.

        :param str name: container name as it appears in the docker compose file.
        """
        log.debug("Unpausing %s container", name)
        container_id = self.get_container_id(name=name)
        self.docker_client.unpause(container_id)

    def stop_container(self, name):
        """Stop the container.

        :param str name: container name as it appears in the docker compose file.
        """
        log.debug("Stopping %s container", name)
        container_id = self.get_container_id(name=name)
        self.docker_client.stop(container_id)

    def start_container(self, name):
        """Start the container.

        :param str name: container name as it appears in the docker compose file.
        """
        log.debug("Starting %s container", name)
        container_id = self.get_container_id(name=name)
        self.docker_client.start(container_id)

    def inspect_container(self, name):
        """Returns the inspect content of a container

        :param name: name of container
        """
        log.debug("Inspecting %s container", name)
        container_id = self.get_container_id(name)
        return self.docker_client.inspect_container(container_id)

    def is_container_ready(self, name):
        """Return True if the container is in ready state.

        If a health check is defined, a healthy container will be considered as ready.
        If no health check is defined, a running container will be considered as ready.

        :param str name: container name as it appears in the docker compose file.
        """
        try:
            status_output = self.inspect_container(name)["State"]
        except RuntimeError:
            return False

        if "Health" in status_output:
            is_ready = status_output["Health"]["Status"] == "healthy"
        else:
            is_ready = status_output["Status"] == "running"

        log.debug("Container %s ready: %s", name, is_ready)
        return is_ready

    def container_status(self, name):
        """Returns container status

        :param str name: container name as it appears in the docker compose file.
        """
        return self.inspect_container(name)["State"]["Status"]

    def wait_for_services(self, services=None, interval=1, timeout=60):
        """Wait for the services checks to pass.

        If the service compose configuration contains an health check, the method will wait for a 'healthy' state.
        If it doesn't the method will wait for a 'running' state.
        """
        services = services if services else self.services
        log.info("Waiting for %s to reach the required state", services)
        checks_callbacks = [partial(self.is_container_ready, name) for name in services]
        return utils.run_health_checks(
            checks=checks_callbacks, interval=interval, timeout=timeout
        )

    @contextmanager
    def container_down(self, name, health_check=None, interval=1, timeout=60):
        """Container down context manager.

        Simulate container down scenario by killing the container within the context,
        once context ends restart the container and wait for the service check to pass.

        :param str name: container name as it appears in the docker compose file.
        :param callable health_check: a callable used to determine if the service has recovered.
        :param int interval: interval (in seconds) between checks.
        :param int timeout: timeout (in seconds) for all checks to pass.

        Usage:

        >>> with controller.service_down(name='consul'):
        >>>     # container will be down in this context
        >>>
        >>> # container will be back up after context end
        """
        container_id = self.get_container_id(name)
        self.docker_client.kill(container_id)
        try:
            yield
        finally:
            self.docker_client.restart(container_id)
            self.wait_for_health(
                name=name, health_check=health_check, interval=interval, timeout=timeout
            )

    @contextmanager
    def container_paused(self, name, health_check=None, interval=1, timeout=60):
        """Container pause context manager.

        Pause the container within the context, once context ends un-pause the container and wait for
        the service check to pass.

        :param str name: container name as it appears in the docker compose file.
        :param callable health_check: a callable used to determine if the service has recovered.
        :param int interval: interval (in seconds) between checks.
        :param int timeout: timeout (in seconds) for all checks to pass.

        Usage:

        >>> with controller.container_paused(name='consul'):
        >>>     # container will be paused in this context
        >>>
        >>> # container will be back up after context end
        """
        container_id = self.get_container_id(name)
        self.docker_client.pause(container_id)
        try:
            yield
        finally:
            self.docker_client.unpause(container_id)
            self.wait_for_health(
                name=name, health_check=health_check, interval=interval, timeout=timeout
            )

    @contextmanager
    def container_stopped(self, name, health_check=None, interval=1, timeout=60):
        """Container stopped context manager.

        Stop the container within the context, once context ends start the container and wait for
        the service check to pass.

        :param str name: container name as it appears in the docker compose file.
        :param callable health_check: a callable used to determine if the service has recovered.
        :param int interval: interval (in seconds) between checks.
        :param int timeout: timeout (in seconds) for all checks to pass.

        Usage:

        >>> with controller.container_stopped(name='consul'):
        >>>     # container will be stopped in this context
        >>>
        >>> # container will be back up after context end
        """
        container_id = self.get_container_id(name)
        self.docker_client.stop(container_id)
        try:
            yield
        finally:
            self.docker_client.start(container_id)
            self.wait_for_health(
                name=name, health_check=health_check, interval=interval, timeout=timeout
            )

    def wait_for_health(self, name, health_check=None, interval=1, timeout=60):
        """Container stopped context manager.

        :param str name: container name as it appears in the docker compose file.
        :param callable health_check: a callable used to determine if the service has recovered.
        :param int interval: interval (in seconds) between checks.
        :param int timeout: timeout (in seconds) for all checks to pass.
        """
        log.debug("Waiting for %s container to be healthy", name)
        health_check = (
            health_check if health_check else lambda: self.is_container_ready(name)
        )
        waiting.wait(health_check, sleep_seconds=interval, timeout_seconds=timeout)

    @staticmethod
    def _get_environment_variables():
        """Set the compose api version according to the server's api version"""
        server_api_version = get_server_api_version()
        log.debug(
            "docker server api version is %s, updating environment_variables",
            server_api_version,
        )
        env = os.environ.copy()
        env["COMPOSE_API_VERSION"] = env["DOCKER_API_VERSION"] = server_api_version
        return env

    def update_plugins(self, message):
        for plugin in self.plugins:
            plugin.update(message=message)

    def get_container_id(self, name):
        """Get container id by name.

        :param str name: container name as it appears in the docker compose file.
        """
        return self.compose.get_service_container_id(name)

    def run_exec_in_container(self, name, command):
        """
        Execute command in container by container name
        :param str name: container name.
        :param str command: command to run in the container.
        """
        log.debug("Creating exec instance in container %s", name)
        container_id = self.get_container_id(name=name)
        exec_create_output = self.docker_client.exec_create(container_id, command)
        if not exec_create_output or not exec_create_output.get("Id"):
            raise RuntimeError("Failed to create exec instance in container %s with command %s" % (name, command))
        exec_id = exec_create_output.get("Id")
        log.debug("Starting exec instance in container %s", name)
        exec_start_output = self.docker_client.exec_start(exec_id)
        if exec_start_output is None:
            raise RuntimeError("Failed to start exec instance in container %s with command %s" % (name, command))
        return exec_start_output
