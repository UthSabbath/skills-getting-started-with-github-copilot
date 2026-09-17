from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module
from src.app import app


client = TestClient(app)
ORIGINAL_ACTIVITIES = deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    original = deepcopy(ORIGINAL_ACTIVITIES)
    app_module.activities.clear()
    app_module.activities.update(deepcopy(original))
    yield
    app_module.activities.clear()
    app_module.activities.update(deepcopy(original))


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data():
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert data["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_for_activity_adds_participant():
    activity_name = "Chess Club"
    email = "student@mergington.edu"

    response = client.post(f"/activities/{quote(activity_name)}/signup?email={email}")

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}

    updated_activity = client.get("/activities").json()[activity_name]
    assert email in updated_activity["participants"]
    assert len(updated_activity["participants"]) == 3


def test_signup_for_existing_student_returns_400():
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    response = client.post(f"/activities/{quote(activity_name)}/signup?email={email}")

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}


def test_signup_for_unknown_activity_returns_404():
    response = client.post("/activities/Unknown Activity/signup?email=test@mergington.edu")

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_participant_from_activity():
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    response = client.delete(f"/activities/{quote(activity_name)}/participants/{email}")

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }

    updated_activity = client.get("/activities").json()[activity_name]
    assert email not in updated_activity["participants"]
    assert len(updated_activity["participants"]) == 1


def test_unregister_missing_participant_returns_404():
    activity_name = "Chess Club"
    email = "missing@mergington.edu"

    response = client.delete(f"/activities/{quote(activity_name)}/participants/{email}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not registered for this activity"}
