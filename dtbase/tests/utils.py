from werkzeug.test import Client


def assert_unauthorized(client: Client, method: str, endpoint: str):
    response = client.open(endpoint, method=method)
    print(response)
    assert response.status_code == 401
