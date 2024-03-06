import re

from flask.testing import FlaskClient


def test_elements(frontend_client: FlaskClient) -> None:
    with frontend_client as client:
        # Get the login page
        response = client.get("/login", follow_redirects=True)

        assert response.status_code == 200

        decode = response.data.decode()

        # Check if there's a form with the username and password inputs
        username_input = re.search(r'<input[^>]*name="email"[^>]*>', decode)
        password_input = re.search(r'<input[^>]*name="password"[^>]*>', decode)
        assert username_input is not None, "Username input not found"
        assert password_input is not None, "Password input not found"

        # Check the login button
        login_button = re.search(r"<button[^>]*name=\"login\"[^>]*>", decode)
        assert login_button is not None, "Login button not found"

        # Find the password toggle button
        eye_button = re.search(
            r"<i[^>]*id=\"show-password\"[^>]*>", response.data.decode()
        )
        assert eye_button is not None, "Password toggle button not found"
