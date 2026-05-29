"""
Root conftest — pytest discovers this file and adds simulator_v1/ to sys.path
automatically, making `from engine.classifier import ...` work in all tests.
Provides session-scoped fixtures shared across test_api.py and test_e2e.py.
"""

import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error

import pytest
from fastapi.testclient import TestClient


# ── Shared API fixture ─────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    """TestClient — loads the CSV once for the entire test session."""
    from main import app
    with TestClient(app) as c:
        yield c


# ── Live server fixture (used only by E2E tests) ───────────────────────────────

def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def _wait_healthy(url: str, retries: int = 30) -> bool:
    for _ in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(1)
    return False


@pytest.fixture(scope="session")
def live_server():
    """
    Ensures the FastAPI server is running on port 8000 for E2E tests.
    If it is already running (started manually), reuses it and does NOT
    shut it down at the end. Otherwise starts uvicorn as a subprocess.
    """
    already_running = _port_open(8000)

    if not already_running:
        import os
        root = os.path.dirname(os.path.abspath(__file__))
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--port", "8000"],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not _wait_healthy("http://localhost:8000/health"):
            proc.terminate()
            pytest.fail("Could not start the live server — health check timed out.")
    else:
        proc = None

    yield "http://localhost:8000"

    if proc is not None:
        proc.terminate()
        proc.wait()
