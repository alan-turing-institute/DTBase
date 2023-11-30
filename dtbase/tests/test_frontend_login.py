from bs4 import BeautifulSoup
from flask.testing import FlaskClient


def test_elements(frontend_client: FlaskClient) -> None:
    with frontend_client as client:
        # Get the login page
        response = client.get("/login", follow_redirects=True)

        assert response.status_code == 200

        soup = BeautifulSoup(response.data, "html.parser")

        # Check if there's a form with the username and password inputs
        username_input = soup.find("input", {"name": "email"})
        password_input = soup.find("input", {"name": "password"})
        assert username_input is not None, "Username input not found"
        assert password_input is not None, "Password input not found"

        # Check the login button
        login_button = soup.find("button", {"name": "login"})
        assert login_button is not None, "Login button not found"

        # Find the password toggle button
        eye_button = soup.find("i", {"id": "show-password"})
        assert eye_button is not None, "Password toggle button not found"


def test_login(frontend_client: FlaskClient) -> None:
    with frontend_client as client:
        from dtbase.core.constants import DEFAULT_USER_EMAIL, DEFAULT_USER_PASSWORD
        from dtbase.tests.conftest import get_csrf_token

        token = get_csrf_token(client)
        print(token, DEFAULT_USER_EMAIL, DEFAULT_USER_PASSWORD)


#        path = "../../.secrets/dtenv_localdb.sh"
#        key = "DT_DEFAULT_USER_PASS"
#        result = subprocess.run(f". {path} && echo ${key}", shell=True,
#                            stdout=subprocess.PIPE)
#        password = result.stdout.decode("utf-8").strip()
#        email = "default_user@localhost"
#        password = "password"
#        type_data = {"email": email, "password": password}
#
#        response = client.post('/login', data=type_data)
#        print(response.json)
