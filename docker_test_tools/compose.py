import subprocess

from docker_test_tools import utils


class Compose:
    def __init__(self, compose_path, project_name, environment_variables, command):
        self.__environment_variables = environment_variables
        self.command = command.split(" ") + ["-f", compose_path, "-p", project_name]
        self.logs_process = None

    def get_services(self):
        return self.__try_run_or_raise(
            command_args=["config", "--services"],
            error_message="Failed getting the compose services",
        ).split("\n")

    def up(self):
        self.__try_run_or_raise(
            command_args=["up", "--build", "-d"],
            error_message="Failed up the compose services",
            stderr=subprocess.STDOUT,
        )

    def down(self):
        self.__try_run_or_raise(
            command_args=["down"],
            error_message="Failed down the compose services",
            stderr=subprocess.STDOUT,
        )

    def get_service_container_id(self, service_name):
        return self.__try_run_or_raise(
            command_args=["ps", "-q", service_name],
            error_message="Failed getting the compose service container id",
        )

    def start_logs_collector(self, stdout):
        """Start a log collection process which writes docker-compose logs into a stdout.

        stdout: stream to write the logs to.
        """
        cmd = self.command + [
            "logs",
            "--no-color",
            "-f",
            "-t",
        ]
        self.logs_process = subprocess.Popen(
            cmd,
            stdout=stdout,
            env=self.__environment_variables,
        )

    def stop_logs_collector(self):
        """Stop the log collection process."""
        if self.logs_process:
            self.logs_process.kill()
            self.logs_process.wait()

    def __try_run_or_raise(self, command_args, error_message, stderr=None):
        try:
            return self.__run_command(command_args, stderr=stderr)
        except subprocess.CalledProcessError as error:
            raise RuntimeError(
                error_message + ", reason: {0}".format(utils.to_str(error.output))
            )

    def __run_command(self, command_args, stderr=None):
        cmd = self.command + command_args
        services_output = subprocess.check_output(
            cmd, stderr=stderr, env=self.__environment_variables
        )
        return utils.to_str(services_output).strip()
