import uuid
from fastapi.testclient import TestClient
from src.app import app, activities


client = TestClient(app)


def make_unique_email(prefix: str = "test") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def test_get_activities_returns_seed_data():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    # Basic shape and known keys
    assert isinstance(data, dict)
    for key in ["Chess Club", "Programming Class", "Gym Class"]:
        assert key in data


def test_signup_adds_participant_and_is_listed_then_cleanup():
    email = make_unique_email("signup")
    activity = "Chess Club"

    # Sign up
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 200
    assert email in activities[activity]["participants"]

    # Verify via GET
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert email in data[activity]["participants"]

    # Cleanup by unregistering
    resp = client.delete(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 200
    assert email not in activities[activity]["participants"]


def test_unregister_nonexistent_participant_returns_404():
    email = make_unique_email("absent")
    activity = "Programming Class"

    resp = client.delete(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 404
    detail = resp.json().get("detail")
    assert "Participant not found" in detail


def test_signup_nonexistent_activity_returns_404():
    email = make_unique_email("ghost")
    resp = client.post("/activities/NotARealActivity/signup", params={"email": email})
    assert resp.status_code == 404
    assert resp.json().get("detail") == "Activity not found"


def test_unregister_nonexistent_activity_returns_404():
    email = make_unique_email("ghostdel")
    resp = client.delete("/activities/NotARealActivity/signup", params={"email": email})
    assert resp.status_code == 404
    assert resp.json().get("detail") == "Activity not found"
import os
import sys
from copy import deepcopy

# Ensure we can import the FastAPI app from src/
CURRENT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import app as app_module  # type: ignore
from fastapi.testclient import TestClient

client = TestClient(app_module.app)


def snapshot_state():
    return {name: list(details["participants"]) for name, details in app_module.activities.items()}


def restore_state(snapshot):
    for name, participants in snapshot.items():
        app_module.activities[name]["participants"] = list(participants)


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"].endswith("/static/index.html")


def test_get_activities_lists_defaults():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    # Basic shape checks
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "Programming Class" in data
    chess = data["Chess Club"]
    assert "participants" in chess and isinstance(chess["participants"], list)


def test_signup_and_unregister_flow():
    snap = snapshot_state()
    try:
        activity = "Chess Club"
        email = "newstudent@mergington.edu"

        # Ensure starting state doesn't have the email
        assert email not in app_module.activities[activity]["participants"]

        # Signup
        r = client.post(f"/activities/{activity}/signup", params={"email": email})
        assert r.status_code == 200
        assert "Signed up" in r.json().get("message", "")

        # Verify present via API
        r2 = client.get("/activities")
        assert r2.status_code == 200
        data = r2.json()
        assert email in data[activity]["participants"]

        # Unregister
        r3 = client.delete(f"/activities/{activity}/signup", params={"email": email})
        assert r3.status_code == 200
        assert "Removed" in r3.json().get("message", "")

        # Verify removed via API
        r4 = client.get("/activities")
        assert r4.status_code == 200
        data2 = r4.json()
        assert email not in data2[activity]["participants"]
    finally:
        restore_state(snap)


def test_unregister_not_found_errors():
    snap = snapshot_state()
    try:
        # Nonexistent activity
        r = client.delete("/activities/DoesNotExist/signup", params={"email": "x@y.com"})
        assert r.status_code == 404
        assert r.json().get("detail") == "Activity not found"

        # Activity exists but participant not in list
        activity = "Gym Class"
        email = "missing@mergington.edu"
        assert email not in app_module.activities[activity]["participants"]
        r2 = client.delete(f"/activities/{activity}/signup", params={"email": email})
        assert r2.status_code == 404
        assert r2.json().get("detail") == "Participant not found for this activity"
    finally:
        restore_state(snap)
