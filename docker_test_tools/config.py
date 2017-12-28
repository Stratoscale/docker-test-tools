import os
from six.moves import configparser


class Config(object):
    """Configuration for docker test tools.

    Test configuration include the following options:

    * Docker logs path.
    * Compose project name.
    * Docker compose file path.
    * Whether or not to keep containers between test runs [True/ False].

    The configuration may be set via:

    1) Constructor variables.
    2) Configuration file (overrides constructor configurations).
    3) Environment variables (overrides constructor variables & file configurations).

    Configuration file should be in the following section & options:

        [environment]
        log-path = <docker log path>
        project-name = <compose project name>
        docker-compose-path = <docker compose path>
        reuse-containers = <True/ False>.

    Supported environment variables:

        DTT_LOG_PATH = <docker log path>
        DTT_PROJECT_NAME = <compose project name>
        DTT_COMPOSE_PATH = <docker compose path>
        DTT_REUSE_CONTAINERS = <1/0>.
        DTT_COLLECT_STATS = <1/0>

    """
    # Expected section name in the configuration file
    SECTION_NAME = 'environment'

    # Expected options in the configuration file
    LOG_PATH_OPTION = 'log-path'
    PROJECT_NAME_OPTION = 'project-name'
    REUSE_CONTAINERS_OPTION = 'reuse-containers'
    DOCKER_COMPOSE_PATH_OPTION = 'docker-compose-path'
    COLLECT_STATS_OPTION = 'collect-stats'

    # Expected options in the configuration file
    LOG_PATH_ENV_VAR = 'DTT_LOG_PATH'
    PROJECT_NAME_ENV_VAR = 'DTT_PROJECT_NAME'
    REUSE_CONTAINERS_ENV_VAR = 'DTT_REUSE_CONTAINERS'
    DOCKER_COMPOSE_PATH_ENV_VAR = 'DTT_COMPOSE_PATH'
    COLLECT_STATS_ENV_VAR = 'DTT_COLLECT_STATS'

    # Configuration default values
    DEFAULT_LOG_PATH = 'docker-tests.log'
    DEFAULT_PROJECT_NAME = 'docker-tests'
    DEFAULT_REUSE_CONTAINERS = False
    DEFAULT_DOCKER_COMPOSE_PATH = 'docker-compose.yml'
    DEFAULT_COLLECT_STATS = False

    def __init__(self,
                 config_path=None,
                 log_path=DEFAULT_LOG_PATH,
                 project_name=DEFAULT_PROJECT_NAME,
                 collect_stats=DEFAULT_COLLECT_STATS,
                 reuse_containers=DEFAULT_REUSE_CONTAINERS,
                 docker_compose_path=DEFAULT_DOCKER_COMPOSE_PATH):

        # Set default values
        self.log_path = log_path
        self.project_name = project_name
        self.collect_stats = collect_stats
        self.reuse_containers = reuse_containers
        self.docker_compose_path = docker_compose_path

        # Update the config values based on the config file (overrides constructor configurations)
        if config_path:
            self.get_file_config(config_path=config_path)

        # Update the config values based on env variables (overrides constructor variables & file configurations)
        self.get_env_config()

    def get_env_config(self):
        """Update the config values based on env variables."""
        self.log_path = os.environ.get(self.LOG_PATH_ENV_VAR, self.log_path)
        self.project_name = os.environ.get(self.PROJECT_NAME_ENV_VAR, self.project_name)
        self.collect_stats = os.environ.get(self.COLLECT_STATS_ENV_VAR, self.collect_stats)
        self.reuse_containers = os.environ.get(self.REUSE_CONTAINERS_ENV_VAR, self.reuse_containers)
        self.docker_compose_path = os.environ.get(self.DOCKER_COMPOSE_PATH_ENV_VAR, self.docker_compose_path)

    def get_file_config(self, config_path):
        """Update the config values based on the config file."""
        if not os.path.exists(config_path):
            raise RuntimeError("Invalid configuration path: %s" % config_path)

        config_reader = configparser.ConfigParser()
        config_reader.read(config_path)
        read_options = config_reader.options(self.SECTION_NAME)

        if self.REUSE_CONTAINERS_OPTION in read_options:
            self.reuse_containers = config_reader.getboolean(self.SECTION_NAME, self.REUSE_CONTAINERS_OPTION)

        if self.COLLECT_STATS_OPTION in read_options:
            self.collect_stats = config_reader.getboolean(self.SECTION_NAME, self.COLLECT_STATS_OPTION)

        if self.PROJECT_NAME_OPTION in read_options:
            self.project_name = config_reader.get(self.SECTION_NAME, self.PROJECT_NAME_OPTION)

        if self.LOG_PATH_OPTION in read_options:
            self.log_path = config_reader.get(self.SECTION_NAME, self.LOG_PATH_OPTION)

        if self.DOCKER_COMPOSE_PATH_OPTION in read_options:
            self.docker_compose_path = config_reader.get(self.SECTION_NAME, self.DOCKER_COMPOSE_PATH_OPTION)
