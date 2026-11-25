import logging
from datetime import timedelta
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.db.database import get_db
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse
from app.api.deps import get_current_user, require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


@lru_cache(maxsize=1)
def _dummy_hash() -> str:
    return get_password_hash("not-a-real-password")


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, returning a JSON Web Token.
    Validates credentials against the stored bcrypt hash. Accounts are never
    created implicitly; an administrator provisions them via `POST /auth/users`.
    """
    if not form_data.username or not form_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password must not be empty",
        )

    user = db.query(User).filter(User.username == form_data.username).first()

    # Always verify a hash so unknown users cannot be told apart by response time.
    password_ok = verify_password(
        form_data.password, user.hashed_password if user else _dummy_hash()
    )
    if user is None or not password_ok:
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


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Creates an account with an explicit role. Administrators only."""
    user = User(
        username=payload.username,
        hashed_password=get_password_hash(payload.password),
        role=payload.role.value,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    db.refresh(user)
    logger.info("User %s created with role %s by %s", user.username, user.role, admin.username)
    return user

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Returns the profile and role of the currently authenticated user.
    """
    return current_user
