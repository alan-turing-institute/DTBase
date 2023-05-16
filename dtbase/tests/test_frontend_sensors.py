"""
Test that the DTBase sensors pages load
"""
from flask import url_for, request
import pytest

from dtbase.core.db_docker import check_for_docker


def test_sensors_index_no_backend(frontend_client):
    with frontend_client:
        response = frontend_client.get("/sensors/index", follow_redirects=True)
        assert response.status_code == 200
        html_content = response.data.decode("utf-8")
        print(html_content)
        assert "Backend API not found" in html_content
