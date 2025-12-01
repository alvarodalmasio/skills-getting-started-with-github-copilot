import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient


# Allow importing `src.app` when running pytest from repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.app import app, activities  # noqa: E402


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities_after_test():
    snapshot = {name: list(d["participants"]) for name, d in activities.items()}
    try:
        yield
    finally:
        for name, participants in snapshot.items():
            activities[name]["participants"] = list(participants)


def make_unique_email(prefix: str = "test") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def test_root_redirects_to_static_index(client: TestClient):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"].endswith("/static/index.html")


def test_get_activities_lists_defaults(client: TestClient):
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data and "Programming Class" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_and_unregister_flow(client: TestClient):
    activity = "Chess Club"
    email = make_unique_email("signup")

    r = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert r.status_code == 200
    assert email in activities[activity]["participants"]

    r2 = client.get("/activities")
    assert r2.status_code == 200
    assert email in r2.json()[activity]["participants"]

    r3 = client.delete(f"/activities/{activity}/signup", params={"email": email})
    assert r3.status_code == 200
    assert email not in activities[activity]["participants"]


def test_not_found_cases(client: TestClient):
    email = make_unique_email("ghost")

    # Nonexistent activity for signup
    r = client.post("/activities/NotARealActivity/signup", params={"email": email})
    assert r.status_code == 404
    assert r.json().get("detail") == "Activity not found"

    # Nonexistent activity for delete
    r2 = client.delete("/activities/NotARealActivity/signup", params={"email": email})
    assert r2.status_code == 404
    assert r2.json().get("detail") == "Activity not found"

    # Existing activity but participant absent
    r3 = client.delete("/activities/Programming Class/signup", params={"email": email})
    assert r3.status_code == 404
    assert "Participant not found" in r3.json().get("detail", "")
