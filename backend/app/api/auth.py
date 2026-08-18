"""Registration, login, logout, and current-user REST endpoints."""

from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import AuthenticatedUser, get_current_auth, get_current_user
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.database.session import get_db
from app.models.revoked_token import RevokedToken
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.category_service import create_default_categories

router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_settings()


def _token_response(user: User) -> TokenResponse:
    token, _, _ = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account and start a secure session",
)
def register_account(payload: RegisterRequest, session: Session = Depends(get_db)) -> TokenResponse:
    existing = session.scalar(select(User.id).where(User.email == str(payload.email)))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")

    user = User(name=payload.name, email=str(payload.email), password_hash=hash_password(payload.password))
    session.add(user)
    try:
        session.flush()
        create_default_categories(session, user.id)
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.") from exc
    session.refresh(user)
    return _token_response(user)


@router.post("/login", response_model=TokenResponse, summary="Sign in with email and password")
def login(payload: LoginRequest, session: Session = Depends(get_db)) -> TokenResponse:
    user = session.scalar(select(User).where(User.email == str(payload.email)))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or password is incorrect.")
    return _token_response(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="End the current JWT session")
def logout(
    auth: AuthenticatedUser = Depends(get_current_auth),
    session: Session = Depends(get_db),
) -> Response:
    session.add(
        RevokedToken(
            jti=auth.token_id,
            user_id=auth.user.id,
            expires_at=auth.expires_at.astimezone(UTC),
        )
    )
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse, summary="Get the signed-in user")
def get_my_profile(current_user: User = Depends(get_current_user)) -> User:
    return current_user
