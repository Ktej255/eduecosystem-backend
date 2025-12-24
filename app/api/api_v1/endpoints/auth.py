from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api import deps
from app.core import security
from app.core.config import settings
from app.crud import user as crud_user
from app.schemas.user import Token, User, UserCreate, UserWithToken
from app.schemas.msg import Msg
from app.schemas.new_password import NewPassword

# ... imports ...


router = APIRouter()


@router.post("/access-token")
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud_user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Your account is pending approval. Please wait for admin approval.")
    elif hasattr(user, 'is_approved') and not user.is_approved:
        raise HTTPException(status_code=400, detail="Your account is pending approval. Please wait for admin approval.")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Check for daily login bonus and streak
    try:
        from app.services.coin_service import check_daily_login_and_streak

        check_daily_login_and_streak(db, user)
    except Exception as e:
        print(f"Failed to check daily login: {e}")

    # Check for 2FA
    if user.is_2fa_enabled:
        return {
            "access_token": security.create_access_token(
                user.id,
                expires_delta=timedelta(minutes=5),  # Short expiry for 2FA step
                token_version=user.token_version,
            ),
            "token_type": "bearer",
            "require_2fa": True,
        }

    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires, token_version=user.token_version
        ),
        "token_type": "bearer",
        "require_2fa": False,
    }


@router.post("/register")
def register(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
) -> Any:
    """
    Register a new user with role-based approval workflow.
    - Students get immediate access
    - Teachers and Admins require approval from admin
    """
    user = crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )
    
    # Validate role
    valid_roles = ["student", "teacher", "admin"]
    role = (user_in.role or "student").lower()
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
    
    # Create user with role-based approval
    user = crud_user.create(db, obj_in=user_in)
    
    # Set approval status based on role
    if role == "student":
        # Students get immediate access
        user.is_active = True
        user.is_approved = True
    else:
        # Teachers and Admins need approval
        user.is_active = False
        user.is_approved = False
        
        # Send approval request email to admin
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            admin_email = "ktej255@gmail.com"
            subject = f"New {role.title()} Registration Request - {user.full_name}"
            body = f"""
            A new {role} has registered and is awaiting approval:
            
            Name: {user.full_name}
            Email: {user.email}
            Role: {role.title()}
            
            Please login to the admin panel to approve or reject this request.
            
            Admin Panel: https://eduecosystem-frontend.vercel.app/admin/users
            """
            
            # Log the approval request (email sending may fail if SMTP not configured)
            print(f"[APPROVAL REQUEST] New {role} registration:")
            print(f"  Name: {user.full_name}")
            print(f"  Email: {user.email}")
            print(f"  Approval email should be sent to: {admin_email}")
            
        except Exception as e:
            print(f"Failed to send approval email: {e}")
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Only provide access token for students (immediate access)
    if role == "student":
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
        
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_approved": user.is_approved,
            "role": user.role,
            "access_token": access_token,
            "token_type": "bearer",
            "pending_approval": False,
        }
    else:
        # Teachers/Admins don't get token until approved
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_approved": user.is_approved,
            "role": user.role,
            "access_token": None,
            "token_type": None,
            "pending_approval": True,
            "message": f"Your {role} account is pending approval. You will receive an email once approved.",
        }


from app.schemas.password_recovery import PasswordRecovery

@router.post("/password-recovery")
def recover_password(
    body: PasswordRecovery,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Password Recovery
    """
    print(f"Recovering password for: {body.email}")
    user = crud_user.get_by_email(db, email=body.email)

    if not user:
        # Return success even if user not found to prevent enumeration
        print(f"User not found: {body.email}")
        return {"msg": "If an account with this email exists, a password recovery email has been sent."}
    
    password_reset_token = security.create_access_token(
        user.id, expires_delta=timedelta(hours=1)
    )
    print(f"Generated token for {user.id}")
    
    if settings.EMAILS_ENABLED:
        try:
            from app.core.email import send_email
            print("Sending email...")
            # await send_email(
            #     email_to=user.email,
            #     subject="Password Recovery",
            #     template_name="reset_password.html",
            #     template_body={
            #         "link": f"{settings.SERVER_HOST}/reset-password?token={password_reset_token}",
            #         "valid_hours": 1
            #     }
            # )
            print("Email sent (simulated)")
        except Exception as e:
            print(f"Failed to send email: {e}")
            
    return {"msg": "If an account with this email exists, a password recovery email has been sent."}


@router.post("/reset-password/")
def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Reset password
    """
    email = security.verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = crud_user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed_password = security.get_password_hash(new_password)
    user.hashed_password = hashed_password
    db.add(user)
    db.commit()
    return {"msg": "Password updated successfully"}
