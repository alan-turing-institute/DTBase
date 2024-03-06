from fastapi.testclient import TestClient
from httpx import Response

TEST_USER_EMAIL = "test@test.com"
TEST_USER_PASSWORD = "test"


def get_token(
    client: TestClient, email: str = TEST_USER_EMAIL, password: str = TEST_USER_PASSWORD
) -> Response:
    """Get an authentication token.

    By default uses the test user, defined above, but email and password can also be
    provided as keyword arguments.
    """
    type_data = {"email": email, "password": password}
    response = client.post("/auth/login", json=type_data)
    return response


def can_login(
    client: TestClient, email: str = TEST_USER_EMAIL, password: str = TEST_USER_PASSWORD
) -> bool:
    """Return true if the given credentials can be used to log in."""
    response = get_token(client, email=email, password=password)
    body = response.json
    return (
        response.status_code == 200
        and body is not None
        and set(body().keys()) == {"access_token", "refresh_token"}
    )


def assert_unauthorized(client: TestClient, method: str, endpoint: str) -> None:
    """Assert that calling the given endpoint with the given client returns 401."""
    method_func = getattr(client, method)
    response = method_func(endpoint)
    assert response.status_code == 401
