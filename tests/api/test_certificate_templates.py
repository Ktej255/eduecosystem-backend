import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.certificate_template import CertificateTemplate


@pytest.fixture
def creator_user(db: Session) -> User:
    """Create a template creator user"""
    from app.core.security import get_password_hash
    from app.models.permissions import Role, Permission

    # Create permission
    perm = Permission(
        name="create_certificate_template",
        display_name="Create Certificate Template",
        resource="certificate_template",
        action="create",
    )
    db.add(perm)
    db.commit()

    # Create role
    role = Role(name="instructor", display_name="Instructor", is_system_role=True)
    role.permissions.append(perm)
    db.add(role)
    db.commit()

    user = User(
        email="creator_template@test.com",
        username="creator_template",
        hashed_password=get_password_hash("password"),
        full_name="Template Creator",
        role="instructor",  # Legacy field
        is_active=True,
    )
    user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_create_certificate_template(
    client: TestClient, db: Session, creator_user: User
):
    """Test creating a new certificate template"""
    # Login
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": creator_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create template
    response = client.post(
        "/api/v1/certificate-templates/",
        json={
            "name": "Modern Blue Template",
            "description": "A modern blue-themed certificate",
            "background_color": "#1e3a8a",
            "title_font": "Georgia",
            "title_font_size": 48,
            "title_color": "#ffffff",
            "body_font": "Arial",
            "body_font_size": 24,
            "body_color": "#e5e7eb",
            "border_style": "simple",
            "border_color": "#60a5fa",
            "is_public": True,
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Modern Blue Template"
    assert data["background_color"] == "#1e3a8a"
    assert data["creator_id"] == creator_user.id
    assert data["is_public"] is True


def test_get_all_templates(client: TestClient, db: Session, creator_user: User):
    """Test retrieving all public templates"""
    # Create templates
    template1 = CertificateTemplate(
        name="Template 1", creator_id=creator_user.id, is_public=True
    )
    template2 = CertificateTemplate(
        name="Template 2", creator_id=creator_user.id, is_public=True
    )
    template3 = CertificateTemplate(
        name="Private Template", creator_id=creator_user.id, is_public=False
    )
    db.add_all([template1, template2, template3])
    db.commit()

    # Get all templates (public only by default)
    response = client.get("/api/v1/certificate-templates/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # At least our 2 public templates


def test_get_my_templates(client: TestClient, db: Session, creator_user: User):
    """Test getting templates created by current user"""
    # Create templates
    for i in range(3):
        template = CertificateTemplate(
            name=f"My Template {i + 1}",
            creator_id=creator_user.id,
            is_public=(i % 2 == 0),
        )
        db.add(template)
    db.commit()

    # Login
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": creator_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get my templates
    response = client.get("/api/v1/certificate-templates/my-templates", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


def test_update_template(client: TestClient, db: Session, creator_user: User):
    """Test updating a certificate template"""
    # Create template
    template = CertificateTemplate(
        name="Original Name",
        description="Original description",
        creator_id=creator_user.id,
        background_color="#ffffff",
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    # Login
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": creator_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update template
    response = client.put(
        f"/api/v1/certificate-templates/{template.id}",
        json={"name": "Updated Name", "background_color": "#000000"},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["background_color"] == "#000000"


@pytest.fixture
def admin_user(db: Session) -> User:
    """Create an admin user"""
    from app.core.security import get_password_hash
    from app.models.permissions import Role

    # Check if admin role exists
    role = db.query(Role).filter(Role.name == "admin").first()
    if not role:
        role = Role(name="admin", display_name="Administrator", is_system_role=True)
        db.add(role)
        db.commit()

    user = User(
        email="admin_template@test.com",
        username="admin_template",
        hashed_password=get_password_hash("password"),
        full_name="Template Admin",
        role="admin",
        is_active=True,
    )
    user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_set_default_template(
    client: TestClient, db: Session, creator_user: User, admin_user: User
):
    """Test setting a template as default"""
    # Create template
    template = CertificateTemplate(
        name="Default Template", creator_id=creator_user.id, is_default=False
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    # Login as admin
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": admin_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Set as default
    response = client.post(
        f"/api/v1/certificate-templates/{template.id}/set-default", headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_default"] is True


def test_get_default_template(client: TestClient, db: Session, creator_user: User):
    """Test retrieving the default template"""
    # Create and set default template
    template = CertificateTemplate(
        name="System Default", creator_id=creator_user.id, is_default=True
    )
    db.add(template)
    db.commit()

    # Get default template
    response = client.get("/api/v1/certificate-templates/default")

    assert response.status_code == 200
    data = response.json()
    assert data["is_default"] is True
    assert data["name"] == "System Default"


def test_delete_template(client: TestClient, db: Session, creator_user: User):
    """Test deleting a non-default template"""
    # Create template
    template = CertificateTemplate(
        name="Template to Delete", creator_id=creator_user.id, is_default=False
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    # Login
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": creator_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Delete template
    response = client.delete(
        f"/api/v1/certificate-templates/{template.id}", headers=headers
    )

    assert response.status_code == 200

    # Verify deleted
    deleted = (
        db.query(CertificateTemplate)
        .filter(CertificateTemplate.id == template.id)
        .first()
    )
    assert deleted is None


def test_cannot_delete_default_template(
    client: TestClient, db: Session, creator_user: User
):
    """Test that default template cannot be deleted"""
    # Create default template
    template = CertificateTemplate(
        name="Default Template", creator_id=creator_user.id, is_default=True
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    # Login
    login_response = client.post(
        "/api/v1/login/access-token",
        data={"username": creator_user.email, "password": "password"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Try to delete (should fail)
    response = client.delete(
        f"/api/v1/certificate-templates/{template.id}", headers=headers
    )

    assert response.status_code == 400
    assert "default" in response.json()["detail"].lower()
