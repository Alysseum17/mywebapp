from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def mock_db():
    with (
        patch("app.routers.items.database.get_connection") as mock_get_conn,
        patch("app.routers.health.database.is_ready") as mock_is_ready,
    ):
        mock_is_ready.return_value = True

        connection = MagicMock()
        cursor = MagicMock()
        connection.cursor.return_value = cursor
        mock_get_conn.return_value = connection

        yield {
            "get_connection": mock_get_conn,
            "connection": connection,
            "cursor": cursor,
            "is_ready": mock_is_ready,
        }


@pytest.fixture
def client(mock_db):
    app = create_app()
    return TestClient(app)
