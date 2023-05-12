"""
Test that the DTBase homepage loads
"""

import pytest

from dtbase.core.db_docker import check_for_docker


DOCKER_RUNNING = check_for_docker()


@pytest.mark.skipif(not DOCKER_RUNNING, reason="requires docker")
def test_home(client):
    response = client.get("/home/index")
    assert response.status_code == 200
