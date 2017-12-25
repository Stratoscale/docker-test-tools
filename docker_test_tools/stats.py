import io
import os
import sys
import json
import logging
import subprocess
import humanfriendly

from docker_test_tools import utils

log = logging.getLogger(__name__)


class StatsCollector(object):
    """Utility for containers stats collection."""

    FORMAT = '{' \
             '"name": "{{.Name}}", ' \
             '"cpu": "{{.CPUPerc}}", ' \
             '"ram": "{{.MemUsage}}", ' \
             '"net": "{{.NetIO}}", ' \
             '"block": "{{.BlockIO}}"' \
             '}'

    def __init__(self, session_name, target_dir_path, project, encoding, environment_variables):
        """Initialize the stats collector."""
        logging.debug("Stats monitor initializing")
        self.project = project
        self.encoding = encoding
        self.environment_variables = environment_variables

        self.work_dir = os.path.join(target_dir_path, 'stats')
        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir)

        self.session_dir = os.path.join(self.work_dir, session_name)
        if not os.path.exists(self.session_dir):
            os.makedirs(self.session_dir)

        self.stats_file_path = os.path.join(self.session_dir, 'stats.json')
        self.stats_summary_path = os.path.join(self.session_dir, 'summary.json')

        self.stats_file = None
        self.stats_process = None

    def start(self):
        """Start a stats collection process which writes docker-compose stats into a file."""
        log.debug("Starting stats collection from environment containers")
        self.stats_file = io.open(self.stats_file_path, 'w', encoding=self.encoding)
        self.stats_process = subprocess.Popen(
            ['docker', 'stats', '--format', self.FORMAT] + self._get_filters(),
            stdout=self.stats_file, env=self.environment_variables,
        )

    def stop(self):
        """Stop the stats collection process and close the stats file."""
        log.debug("Stopping stats collection from environment containers")
        if self.stats_process:
            self.stats_process.kill()
            self.stats_process.wait()

        if self.stats_file:
            self.stats_file.close()
            with open(self.stats_summary_path, 'a') as target:
                cluster_stats = ClusterStats(stat_file_path=self.stats_file_path, encoding=self.encoding).to_dict()
                json.dump(cluster_stats, target, sort_keys=True, indent=2)

    def _get_filters(self):
        """Return the docker-compose project containers."""
        filters_output = subprocess.check_output(
            ['docker', 'ps', '--format', '{{.Names}}',
             '--filter', "label=com.docker.compose.project={project}".format(project=self.project)]
        )
        return utils.to_str(filters_output).strip().split('\n')


class ClusterStats(object):
    """Parse and calculate containers cluster session stats."""

    SAMPLE_PREFIX = "\x1b[2J\x1b[H"

    def __init__(self, stat_file_path, encoding):
        self.encoding = encoding
        self.summary_data = {}
        self._split_logs(stat_file_path)

    def parse_file(self, stat_file_path):
        """Parse a collected stats file into an object."""
        output = []

        with open(stat_file_path, 'r') as stat_file:
            for raw_line in stat_file.readlines():
                line = self.parse_line(line=raw_line)
                if line:
                    output.append(line)

        with open(stat_file_path, 'w') as stat_file:
            json.dump(output, stat_file, indent=2)

    def _split_logs(self, stat_file_path):
        """Split the collected docker stats file into a file per service."""
        log.debug("Splitting stats file into separated files per service")
        services_stats = {}
        try:
            with io.open(stat_file_path, 'r', encoding=self.encoding) as combined_stats_file:
                for raw_line in combined_stats_file.readlines():

                    parsed_line = self.parse_line(line=raw_line)
                    if not parsed_line:
                        continue

                    service_name = parsed_line.pop("name")
                    if service_name not in services_stats:
                        services_stats[service_name] = []

                    services_stats[service_name].append(parsed_line)
        finally:
            for service_name, service_stats in services_stats.items():
                with open(stat_file_path + ".{}.json".format(service_name), 'w') as stat_file:
                    json.dump(service_stats, stat_file, indent=2)

    def parse_line(self, line):
        """Parse the stats line.

        - Extract the line data from the raw string.
        - Add the data to the stats summary info.
        """
        # Cleanup escape characters prefix
        line = line.lstrip(self.SAMPLE_PREFIX)

        # Skip bad stats metrics
        if '--' in line:
            return

        # Split the stat data to it's raw components
        components = json.loads(line)

        # Skip bad stats metrics
        if len(components) != 5:
            return

        name = components['name']

        # Get the used CPU percentage as a floating number
        components['cpu'] = float(components['cpu'][:-1])

        # Get the used stats numbers as used bytes number
        components['ram'] = self.get_bytes(components['ram'])
        components['net'] = self.get_bytes(components['net'])
        components['block'] = self.get_bytes(components['block'])

        if name not in self.summary_data:
            self.summary_data[name] = ContainerStats(name=name)

        self.summary_data[name].update(
            cpu_used=components['cpu'],
            ram_used=components['ram'],
            net_io_used=components['net'],
            block_io_used=components['block']
        )

        return components

    @staticmethod
    def get_bytes(raw_value):
        """Get the number as used bytes number"""
        return humanfriendly.parse_size(raw_value.split('/')[0], binary=True)

    def __str__(self):
        """Return a string representation of the collected stats."""
        return str(self.to_dict())

    def to_dict(self):
        """Return a dictionary representation of the collected stats."""
        return {container_summary.name: container_summary.to_dict()
                for container_summary in self.summary_data.values()}


class ContainerStats(object):
    """Parse and calculate a single container session stats."""

    def __init__(self, name):
        """Initialize container stats summary."""
        self.name = name

        self.count = 0

        self.cpu_sum = self.ram_sum = self.net_io_sum = self.block_io_sum = 0
        self.cpu_max = self.ram_max = self.net_io_max = self.block_io_max = 0
        self.cpu_min = self.ram_min = self.net_io_min = self.block_io_min = sys.maxsize

    def update(self, cpu_used, ram_used, net_io_used, block_io_used):
        """Update container stats summary in an iterative manner."""
        self.count += 1
        self.cpu_sum += cpu_used
        self.ram_sum += ram_used
        self.net_io_sum += net_io_used
        self.block_io_sum += block_io_used

        if cpu_used > self.cpu_max:
            self.cpu_max = cpu_used

        if ram_used > self.ram_max:
            self.ram_max = ram_used

        if net_io_used > self.net_io_max:
            self.net_io_max = net_io_used

        if block_io_used > self.block_io_max:
            self.block_io_max = block_io_used

        if cpu_used <= self.cpu_min:
            self.cpu_min = cpu_used

        if ram_used <= self.ram_min:
            self.ram_min = ram_used

        if net_io_used <= self.net_io_min:
            self.net_io_min = net_io_used

        if block_io_used <= self.block_io_min:
            self.block_io_min = block_io_used

    @property
    def cpu_avg(self):
        """Calculate the average cpu usage and return it."""
        if self.count == 0:
            return None

        return self.cpu_sum / self.count

    @property
    def ram_avg(self):
        """Calculate the average ram usage and return it."""
        if self.count == 0:
            return None

        return self.ram_sum / self.count

    @property
    def net_io_avg(self):
        """Calculate the average net_io usage and return it."""
        if self.count == 0:
            return None

        return self.net_io_sum / self.count

    @property
    def block_io_avg(self):
        """Calculate the average block_io usage and return it."""
        if self.count == 0:
            return None

        return self.block_io_sum / self.count

    def __str__(self):
        """Return a string representation of the collected container stats."""
        return str(self.to_dict())

    def to_dict(self):
        return {
            "cpu": {
                "min": self.cpu_min,
                "max": self.cpu_max,
                "avg": self.cpu_avg,

            },
            "ram": {
                "min": humanfriendly.format_size(self.ram_min),
                "max": humanfriendly.format_size(self.ram_max),
                "avg": humanfriendly.format_size(self.ram_avg),

            },
            "net_io": {
                "min": humanfriendly.format_size(self.net_io_min),
                "max": humanfriendly.format_size(self.net_io_max),
                "avg": humanfriendly.format_size(self.net_io_avg),

            },
            "block_io": {
                "min": humanfriendly.format_size(self.block_io_min),
                "max": humanfriendly.format_size(self.block_io_max),
                "avg": humanfriendly.format_size(self.block_io_avg),

            }
        }
