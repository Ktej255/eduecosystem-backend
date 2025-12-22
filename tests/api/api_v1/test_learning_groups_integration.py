import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.models.learning_group import LearningGroup, GroupMembership, MemberRole, GroupType, GroupPrivacy
from app.tests.utils.utils import random_lower_string, random_email
from app.tests.utils.user import create_random_user, authentication_token_from_email

def test_create_learning_group(client: TestClient, db: Session) -> None:
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    user = crud.user.get_by_email(db, email=email)
    
    data = {
        "name": "Test Group",
        "description": "A test group",
        "group_type": "study",
        "privacy": "public"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/learning-groups/groups",
        headers=headers,
        json=data,
    )
    
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]
    assert content["group_type"] == data["group_type"]
    assert content["privacy"] == data["privacy"]
    assert content["member_count"] == 1
    assert content["created_by"] == user.id

def test_get_my_groups(client: TestClient, db: Session) -> None:
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    user = crud.user.get_by_email(db, email=email)
    
    # Create a group
    group = LearningGroup(
        name="My Test Group",
        description="My group description",
        group_type=GroupType.STUDY,
        privacy=GroupPrivacy.PUBLIC,
        created_by=user.id
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    
    # Add membership
    membership = GroupMembership(
        group_id=group.id,
        user_id=user.id,
        role=MemberRole.ADMIN
    )
    db.add(membership)
    db.commit()
    
    response = client.get(
        f"{settings.API_V1_STR}/learning-groups/groups/my",
        headers=headers,
    )
    
    assert response.status_code == 200
    content = response.json()
    assert len(content) >= 1
    assert content[0]["id"] == group.id
    assert content[0]["name"] == group.name

def test_join_group(client: TestClient, db: Session) -> None:
    creator_email = random_email()
    authentication_token_from_email(client=client, email=creator_email, db=db)
    creator = crud.user.get_by_email(db, email=creator_email)
    
    user_email = random_email()
    headers = authentication_token_from_email(client=client, email=user_email, db=db)
    user = crud.user.get_by_email(db, email=user_email)
    
    # Create a group by creator
    group = LearningGroup(
        name="Joinable Group",
        description="Join me",
        group_type=GroupType.STUDY,
        privacy=GroupPrivacy.PUBLIC,
        created_by=creator.id
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    
    # Join the group
    response = client.post(
        f"{settings.API_V1_STR}/learning-groups/groups/{group.id}/join",
        headers=headers,
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Joined group successfully"
    
    # Verify membership
    membership = db.query(GroupMembership).filter(
        GroupMembership.group_id == group.id,
        GroupMembership.user_id == user.id
    ).first()
    assert membership is not None
    assert membership.role == MemberRole.MEMBER
