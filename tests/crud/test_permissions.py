from sqlalchemy.orm import Session
from app.crud import permissions as crud_permissions
from app.schemas import permissions as schemas


def test_create_permission(db: Session):
    permission_in = schemas.PermissionCreate(
        name="test_permission",
        display_name="Test Permission",
        description="A test permission",
        resource="test",
        action="test",
    )
    permission = crud_permissions.create_permission(db, permission_in)
    assert permission.name == "test_permission"
    assert permission.resource == "test"
    assert permission.action == "test"


def test_create_role(db: Session):
    role_in = schemas.RoleCreate(
        name="test_role", display_name="Test Role", description="A test role"
    )
    role = crud_permissions.create_role(db, role_in)
    assert role.name == "test_role"
    assert role.display_name == "Test Role"


def test_assign_role_to_user(db: Session, test_user):
    # Create role
    role_in = schemas.RoleCreate(
        name="assign_test_role", display_name="Assign Test Role"
    )
    role = crud_permissions.create_role(db, role_in)

    # Assign to user
    crud_permissions.assign_role_to_user(db, user_id=test_user.id, role_id=role.id)

    # Verify
    user_roles = crud_permissions.get_user_roles(db, user_id=test_user.id)
    assert len(user_roles) >= 1
    assert any(r.id == role.id for r in user_roles)

    # Check role check
    assert crud_permissions.check_role(
        db, user_id=test_user.id, role_name="assign_test_role"
    )


def test_check_permission(db: Session, test_user):
    # Create permission
    perm_in = schemas.PermissionCreate(
        name="check_perm_test",
        display_name="Check Perm Test",
        resource="test",
        action="check",
    )
    permission = crud_permissions.create_permission(db, perm_in)

    # Create role
    role_in = schemas.RoleCreate(
        name="perm_role", display_name="Perm Role", permission_ids=[permission.id]
    )
    role = crud_permissions.create_role(db, role_in)

    # Assign role to user
    crud_permissions.assign_role_to_user(db, user_id=test_user.id, role_id=role.id)

    # Check permission
    assert crud_permissions.check_permission(
        db, user_id=test_user.id, permission_name="check_perm_test"
    )
    assert not crud_permissions.check_permission(
        db, user_id=test_user.id, permission_name="non_existent_perm"
    )
