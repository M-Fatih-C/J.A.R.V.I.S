"""Explicit offline substitutes for health-route contract tests only."""

import pytest

from jarvis.api.dependencies import get_mlx_client, get_ollama_client, get_short_term_memory
from jarvis.api.main import app


class UnavailableService:
    async def health_check(self):
        return False

    async def ping(self):
        return False


@pytest.fixture
def offline_health_dependencies():
    dependencies = (get_mlx_client, get_ollama_client, get_short_term_memory)
    previous = {dep: app.dependency_overrides.get(dep) for dep in dependencies}
    for dep in dependencies:
        app.dependency_overrides[dep] = UnavailableService
    try:
        yield
    finally:
        for dep, value in previous.items():
            if value is None:
                app.dependency_overrides.pop(dep, None)
            else:
                app.dependency_overrides[dep] = value
