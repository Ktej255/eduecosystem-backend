from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.utils.user import create_random_user, authentication_token_from_email


def test_create_collaborative_project(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    data = {
        "title": "Test Project",
        "description": "A collaborative project",
        "max_team_size": 3,
        "milestones": [{"title": "Milestone 1", "description": "First step"}],
    }
    response = client.post(
        f"{settings.API_V1_STR}/projects/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["max_team_size"] == 3
    assert len(content["milestones"]) == 1
    assert content["milestones"][0]["title"] == "Milestone 1"
    assert "id" in content


def test_create_team_and_join(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    # 1. Create Project
    project_data = {"title": "Team Project", "max_team_size": 2}
    r = client.post(
        f"{settings.API_V1_STR}/projects/",
        headers=superuser_token_headers,
        json=project_data,
    )
    project_id = r.json()["id"]

    # 2. Create Team (as superuser)
    team_data = {"name": "Alpha Team"}
    r = client.post(
        f"{settings.API_V1_STR}/projects/{project_id}/teams",
        headers=superuser_token_headers,
        json=team_data,
    )
    assert r.status_code == 200
    team_id = r.json()["id"]

    # 3. Create another user to join
    user2 = create_random_user(db)
    user2_token = authentication_token_from_email(
        client=client, email=user2.email, db=db
    )
    user2_headers = {"Authorization": f"Bearer {user2_token}"}

    # 4. Join Team
    r = client.post(
        f"{settings.API_V1_STR}/projects/{project_id}/teams/{team_id}/join",
        headers=user2_headers,
    )
    assert r.status_code == 200
    assert r.json()["message"] == "Joined team successfully"


def test_submit_project(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    # 1. Create Project
    project_data = {"title": "Submission Project"}
    r = client.post(
        f"{settings.API_V1_STR}/projects/",
        headers=superuser_token_headers,
        json=project_data,
    )
    project_id = r.json()["id"]

    # 2. Create Team
    team_data = {"name": "Beta Team"}
    r = client.post(
        f"{settings.API_V1_STR}/projects/{project_id}/teams",
        headers=superuser_token_headers,
        json=team_data,
    )
    team_id = r.json()["id"]

    # 3. Submit
    submission_data = {
        "file_url": "http://example.com/file.zip",
        "description": "Final submission",
    }
    r = client.post(
        f"{settings.API_V1_STR}/projects/{project_id}/teams/{team_id}/submit",
        headers=superuser_token_headers,
        json=submission_data,
    )
    assert r.status_code == 200
    content = r.json()
    assert content["file_url"] == submission_data["file_url"]
    assert content["team_id"] == team_id
