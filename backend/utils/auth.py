"""
Authentication utilities for JWT token management and password hashing
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
from uuid import uuid4

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# In-memory user storage (replace with database in production)
users_db: Dict[str, Dict[str, Any]] = {
    "admin": {
        "id": "user_001",
        "username": "admin",
        "email": "admin@1pwr.com",
        "full_name": "System Administrator",
        "hashed_password": pwd_context.hash("admin123"),  # Default password
        "role": "admin",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    "field_user": {
        "id": "user_002",
        "username": "field_user",
        "email": "field@1pwr.com",
        "full_name": "Field Team Member",
        "hashed_password": pwd_context.hash("field123"),  # Default password
        "role": "field_team",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    "viewer": {
        "id": "user_003",
        "username": "viewer",
        "email": "viewer@1pwr.com",
        "full_name": "Read-Only User",
        "hashed_password": pwd_context.hash("viewer123"),  # Default password
        "role": "viewer",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def get_user(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username"""
    return users_db.get(username)

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    for user in users_db.values():
        if user["id"] == user_id:
            return user
    return None

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Get the current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = get_user(username)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get the current active user"""
    if not current_user.get("is_active"):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def check_permission(user: Dict[str, Any], permission: str) -> bool:
    """Check if a user has a specific permission"""
    from models.user import ROLE_PERMISSIONS, UserRole, UserPermission
    
    user_role = UserRole(user.get("role", "viewer"))
    role_permissions = ROLE_PERMISSIONS.get(user_role, [])
    
    return UserPermission(permission) in role_permissions

def require_permission(permission: str):
    """Dependency to require a specific permission"""
    async def permission_checker(current_user: Dict[str, Any] = Depends(get_current_active_user)):
        if not check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required"
            )
        return current_user
    return permission_checker

def create_user(username: str, email: str, password: str, full_name: str, role: str = "viewer") -> Dict[str, Any]:
    """Create a new user"""
    if username in users_db:
        raise ValueError("Username already exists")
    
    user_id = f"user_{uuid4().hex[:8]}"
    hashed_password = get_password_hash(password)
    
    user = {
        "id": user_id,
        "username": username,
        "email": email,
        "full_name": full_name,
        "hashed_password": hashed_password,
        "role": role,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    users_db[username] = user
    return user

def update_user(username: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update user information"""
    user = get_user(username)
    if not user:
        return None
    
    # Handle password update
    if "password" in updates:
        updates["hashed_password"] = get_password_hash(updates["password"])
        del updates["password"]
    
    # Update fields
    for key, value in updates.items():
        if value is not None:
            user[key] = value
    
    user["updated_at"] = datetime.utcnow()
    return user

def delete_user(username: str) -> bool:
    """Delete a user"""
    if username in users_db:
        del users_db[username]
        return True
    return False

def list_users() -> list:
    """List all users"""
    return [
        {k: v for k, v in user.items() if k != "hashed_password"}
        for user in users_db.values()
    ]
