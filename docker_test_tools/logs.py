import io
import logging
import os

import datetime
import six

log = logging.getLogger(__name__)


class LogCollector(object):
    """Utility for containers log collection."""

    SEPARATOR = "|"
    COMMON_LOG_PREFIX = ">>>"
    COMMON_LOG_FORMAT = six.u("\n{prefix} {time} {{message}}\n\n").format(
        prefix=COMMON_LOG_PREFIX,
        time=datetime.datetime.utcnow().isoformat(),
    )

    def __init__(
        self, log_path, encoding, compose
    ):
        """Initialize the log collector."""
        self.log_path = log_path
        self.encoding = encoding
        self.compose = compose

        self.logs_file = None
        self.logs_process = None

    def start(self):
        """Start a log collection process which writes docker-compose logs into a file."""
        log.debug("Starting logs collection from environment containers")
        self.logs_file = io.open(self.log_path, "w", encoding=self.encoding)
        self.compose.start_logs_collector(self.logs_file)

    def stop(self):
        """Stop the log collection process and close the log file."""
        log.debug("Stopping logs collection from environment containers")
        self.compose.stop_logs_collector()

        if self.logs_file:
            self.logs_file.close()
            self._split_logs()

    def update(self, message):
        """Write a common log message to the container logs."""
        self.logs_file.write(self.COMMON_LOG_FORMAT.format(message=message))
        self.logs_file.flush()

    def _split_logs(self):
        """Split the collected docker-compose log file into a file per service.

        Each line in the collected log file is in a format of: 'service.name_number  | message'
        This method writes each line to it's service log file amd keeps only the message.
        """
        log.debug("Splitting log file into separated files per service")
        services_log_files = {}
        log_dir = os.path.dirname(self.log_path)
        try:
            with io.open(
                self.log_path, "r", encoding=self.encoding
            ) as combined_log_file:
                for log_line in combined_log_file.readlines():
                    # Write common log lines to all log files
                    if log_line.startswith(self.COMMON_LOG_PREFIX):
                        for services_log_file in services_log_files.values():
                            services_log_file.write(
                                six.u("\n{log_line}\n").format(log_line=log_line)
                            )

                    else:
                        # Write each log message to the appropriate log file (by prefix)
                        separator_location = log_line.find(self.SEPARATOR)
                        if separator_location != -1:
                            # split service name from log message
                            service_name = log_line[:separator_location].strip()
                            message = log_line[separator_location + 1:]

                            # Create a log file if one doesn't exists
                            if service_name not in services_log_files:
                                services_log_files[service_name] = io.open(
                                    os.path.join(log_dir, service_name + ".log"),
                                    "w",
                                    encoding=self.encoding,
                                )

                            services_log_files[service_name].write(message)
        finally:
            for services_log_file in services_log_files.values():
                services_log_file.close()
