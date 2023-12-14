def get_server_api_version():
    from docker import APIClient
    client = APIClient(base_url='unix://var/run/docker.sock')
    return client.api_version


if __name__ == '__main__':
    print(get_server_api_version())
