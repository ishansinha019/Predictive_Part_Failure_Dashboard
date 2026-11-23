from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.db.database import get_db
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserResponse
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, returning a JSON Web Token.
    Validates user credentials against stored bcrypt hash in the database.
    Auto-registers new demo users on first valid login for smooth onboarding.
    """
    if not form_data.username or not form_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password must not be empty",
        )

    user = db.query(User).filter(User.username == form_data.username).first()

    if not user:
        # Create user on first login for demo / onboarding convenience
        role = "admin" if form_data.username.lower() in ("admin", "supervisor") else "technician"
        user = User(
            username=form_data.username,
            hashed_password=get_password_hash(form_data.password),
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Verify stored bcrypt hash
        if not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Returns the profile and role of the currently authenticated user.
    """
    return current_user
