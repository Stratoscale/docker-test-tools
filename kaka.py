import subprocess


def get_docker_version():
    """Return the docker engine version."""
    return subprocess.check_output("docker version --format '{{.Server.Version}}'", shell=True).strip()

with open('kaka', 'r') as f:
    for line in f.readlines():
        print line.strip(), line.strip() > '1.12.0'
