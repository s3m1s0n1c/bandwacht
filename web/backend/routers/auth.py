"""Login endpoint."""

from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

from ..auth import create_access_token, verify_password
from ..config import settings

router = APIRouter()


@router.post("/auth/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    if (
        form.username != settings.auth_username
        or not verify_password(form.password, settings.auth_password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falscher Benutzername oder Passwort",
        )
    token = create_access_token(form.username)
    return {"access_token": token, "token_type": "bearer"}
