from datetime import timedelta
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.settings import settings
from app.infrastructure.db.models import UserModel, OrganizationModel
from app.infrastructure.security.auth import get_password_hash, verify_password, create_access_token
from app.domain.entities.tenant import User

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


# DTO Schemas
class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    organization_name: str
    role: str = "recruiter"


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class TokenSchema(BaseModel):
    access_token: str
    token_type: str
    organization_id: UUID
    role: str


class UserMeResponseSchema(BaseModel):
    id: UUID
    email: EmailStr
    organization_id: UUID
    organization_name: str
    role: str


# Authentication dependency
def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        org_id: str = payload.get("org_id")
        role: str = payload.get("role")
        
        if user_id is None or org_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(UserModel).filter(UserModel.id == UUID(user_id)).first()
    if user is None:
        raise credentials_exception
        
    return User(
        id=user.id,
        email=user.email,
        password_hash=user.password_hash,
        role=user.role,
        organization_id=user.organization_id,
        created_at=user.created_at
    )


@router.post("/register", response_model=TokenSchema, status_code=status.HTTP_201_CREATED)
def register(data: RegisterSchema, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(UserModel).filter(UserModel.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # 1. Create Organization
    org = OrganizationModel(name=data.organization_name)
    db.add(org)
    db.commit()
    db.refresh(org)

    # 2. Create User
    hashed_pwd = get_password_hash(data.password)
    user = UserModel(
        email=data.email,
        password_hash=hashed_pwd,
        role=data.role,
        organization_id=org.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 3. Create Token
    token = create_access_token(
        subject=user.id, 
        organization_id=org.id,
        role=user.role
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "organization_id": org.id,
        "role": user.role
    }


@router.post("/login", response_model=TokenSchema)
def login(data: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        subject=user.id,
        organization_id=user.organization_id,
        role=user.role
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "organization_id": user.organization_id,
        "role": user.role
    }


@router.get("/me", response_model=UserMeResponseSchema)
def read_users_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org = db.query(OrganizationModel).filter(OrganizationModel.id == current_user.organization_id).first()
    org_name = org.name if org else "Unknown Organization"
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "organization_id": current_user.organization_id,
        "organization_name": org_name,
        "role": current_user.role
    }
