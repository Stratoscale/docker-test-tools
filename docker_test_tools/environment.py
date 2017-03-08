import logging
import subprocess


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
            logging.warning("container reuse enabled: Skipping environment cleanup")
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

    def get_containers_logs(self):
        """Write the environment containers logs into a file."""
        logging.info("Writing containers logs to %s, using docker compose: %s", self.log_path, self.compose_path)
        try:
            subprocess.check_output(
                'docker-compose -f {compose_path} -p {project_name} logs --no-color > {log_path}'.format(
                    compose_path=self.compose_path, project_name=self.project_name,log_path=self.log_path),
                shell=True, stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as error:
            raise RuntimeError("Failed writing environment containers log, reason: \n%s", error.output)

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
