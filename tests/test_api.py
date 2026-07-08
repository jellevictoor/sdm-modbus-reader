"""
Tests for the FastAPI web interface
"""
import asyncio
from starlette.requests import Request

from sdm_modbus_reader import api


def _make_request(path: str = "/") -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [],
        "query_string": b"",
    }
    return Request(scope)


def test_root_renders_index_page():
    """The home page must render (regression: Starlette TemplateResponse signature)"""
    response = asyncio.run(api.root(_make_request()))

    assert response.status_code == 200
