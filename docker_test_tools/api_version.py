import requests_unixsocket


def get_server_api_version():
    """Return docker server api version using REST API."""
    session = requests_unixsocket.Session()
    server_versions = session.get('http+unix://%2Fvar%2Frun%2Fdocker.sock/version').json()
    return server_versions['ApiVersion']


def get_server_api_version_new():
    from docker import APIClient
    client = APIClient(base_url='unix://var/run/docker.sock')
    print(client.api_version)


if __name__ == '__main__':
    print(get_server_api_version())
    print(get_server_api_version_new())
