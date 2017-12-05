import io
import os
import sys
import logging
import subprocess
import humanfriendly

log = logging.getLogger(__name__)


class StatsCollector(object):
    """Utility for containers stats collection."""

    def __init__(self, session_name, target_dir_path, project, encoding, environment_variables):
        """Initialize the stats collector."""
        logging.debug("Stats monitor initializing")
        self.project = project
        self.encoding = encoding
        self.environment_variables = environment_variables

        self.stats_file_path = os.path.join(target_dir_path, session_name + '.stats')
        self.stats_summary_path = os.path.join(target_dir_path, session_name + '.summary')

        self.stats_file = None
        self.stats_process = None

    def start(self):
        """Start a stats collection process which writes docker-compose stats into a file."""
        log.debug("Starting stats collection from environment containers")
        self.stats_file = io.open(self.stats_file_path, 'w', encoding=self.encoding)
        self.stats_process = subprocess.Popen(
            ['docker', 'stats', '--format', '{{.Name}},{{.CPUPerc}},{{.MemUsage}}'] + self._get_filters(),
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
                target.write(str(ClusterStats(stat_file_path=self.stats_file_path)))

    def _get_filters(self):
        """Return the docker-compose project containers."""
        return subprocess.check_output(
            ['docker', 'ps', '--format', '{{.Names}}',
             '--filter', "label=com.docker.compose.project={project}".format(project=self.project)]
        ).strip().split('\n')


class ClusterStats(object):
    """Parse and calculate containers cluster session stats."""

    SAMPLE_PREFIX = "\x1b[2J\x1b[H"

    def __init__(self, stat_file_path):
        self.summary_data = {}
        self.parse_file(stat_file_path)

    def parse_file(self, stat_file_path):
        """Parse a collected stats file into an object."""
        with open(stat_file_path, 'r') as stat_file:
            for raw_line in stat_file.readlines():
                self.parse_line(line=raw_line)

    def parse_line(self, line):
        """Parse the stats line.

        - Extract the line data from the raw string.
        - Add the data to the stats summary info.
        """
        # Cleanup escape characters prefix
        line = line.lstrip(self.SAMPLE_PREFIX)

        # Split the stat data to it's raw components
        raw_components = line.split(',')

        # Skip bad stats metrics
        if len(raw_components) != 3:
            return

        name, raw_cpu, raw_ram = raw_components

        # Skip bad stats metrics
        if raw_cpu == '--' or raw_ram == '--':
            return

        # Get the used CPU percentage as a floating number
        cpu_used = float(raw_cpu[:-1])

        # Get the used RAM number as used bytes number
        ram_used = humanfriendly.parse_size(raw_ram.split('/')[0], binary=True)
        if name not in self.summary_data:
            self.summary_data[name] = ContainerStats(name=name)

        self.summary_data[name].update(cpu_used=cpu_used, ram_used=ram_used)

    def __str__(self):
        """Return a string representation of the collected stats."""
        return '\n'.join([str(container_summary) for container_summary in self.summary_data.values()])


class ContainerStats(object):
    """Parse and calculate a single container session stats."""

    def __init__(self, name):
        """Initialize container stats summary."""
        self.name = name

        self.count = 0

        self.cpu_sum = 0
        self.ram_sum = 0
        self.cpu_max = 0
        self.ram_max = 0
        self.cpu_min = sys.maxsize
        self.ram_min = sys.maxsize

    def update(self, cpu_used, ram_used):
        """Update container stats summary in an iterative manner."""
        self.count += 1
        self.cpu_sum += cpu_used
        self.ram_sum += ram_used

        if cpu_used > self.cpu_max:
            self.cpu_max = cpu_used

        if ram_used > self.ram_max:
            self.ram_max = ram_used

        if cpu_used <= self.cpu_min:
            self.cpu_min = cpu_used

        if ram_used <= self.ram_min:
            self.ram_min = ram_used

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

    def __str__(self):
        """Return a string representation of the collected container stats."""
        return (
            "container: {name}, "
            "ram min: {ram_min}, ram max: {ram_max}, ram avg: {ram_avg}, "
            "cpu min: {cpu_min}%, cpu max: {cpu_max}%, cpu avg: {cpu_avg:.2f}%".format(
                name=self.name,
                ram_min=humanfriendly.format_size(self.ram_min),
                ram_max=humanfriendly.format_size(self.ram_max),
                ram_avg=humanfriendly.format_size(self.ram_avg),
                cpu_min=self.cpu_min,
                cpu_max=self.cpu_max,
                cpu_avg=self.cpu_avg,

            )
        )
