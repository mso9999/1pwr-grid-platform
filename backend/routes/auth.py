"""
Authentication routes for user login, registration, and token management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Dict, Any

from models.user import (
    UserCreate, UserLogin, Token, User, UserUpdate,
    UserRole, ROLE_PERMISSIONS
)
from utils.auth import (
    authenticate_user, create_access_token, create_refresh_token,
    get_current_active_user, create_user, update_user, delete_user,
    list_users, require_permission, get_user, decode_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, Any]:
    """
    Login endpoint for user authentication
    
    Returns JWT access token on successful authentication
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    
    # Update last login
    user["last_login"] = datetime.utcnow()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/register", response_model=User)
async def register(
    user_data: UserCreate,
    current_user: Dict[str, Any] = Depends(require_permission("manage_users"))
) -> Dict[str, Any]:
    """
    Register a new user (requires manage_users permission)
    """
    try:
        new_user = create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role.value
        )
        
        # Get permissions for role
        role = UserRole(new_user["role"])
        permissions = ROLE_PERMISSIONS.get(role, [])
        
        # Return user without password
        return {
            "id": new_user["id"],
            "username": new_user["username"],
            "email": new_user["email"],
            "full_name": new_user["full_name"],
            "role": new_user["role"],
            "is_active": new_user["is_active"],
            "created_at": new_user["created_at"],
            "updated_at": new_user["updated_at"],
            "last_login": new_user.get("last_login"),
            "permissions": [p.value for p in permissions]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh access token using refresh token
    """
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    username = payload.get("sub")
    user = get_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get current user information
    """
    role = UserRole(current_user["role"])
    permissions = ROLE_PERMISSIONS.get(role, [])
    
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "role": current_user["role"],
        "is_active": current_user["is_active"],
        "created_at": current_user["created_at"],
        "updated_at": current_user["updated_at"],
        "last_login": current_user.get("last_login"),
        "permissions": [p.value for p in permissions]
    }

@router.put("/me", response_model=User)
async def update_current_user(
    updates: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Update current user information
    """
    # Users can only update their own info, not role
    if updates.role is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own role"
        )
    
    updated_user = update_user(current_user["username"], updates.dict(exclude_unset=True))
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    role = UserRole(updated_user["role"])
    permissions = ROLE_PERMISSIONS.get(role, [])
    
    return {
        "id": updated_user["id"],
        "username": updated_user["username"],
        "email": updated_user["email"],
        "full_name": updated_user["full_name"],
        "role": updated_user["role"],
        "is_active": updated_user["is_active"],
        "created_at": updated_user["created_at"],
        "updated_at": updated_user["updated_at"],
        "last_login": updated_user.get("last_login"),
        "permissions": [p.value for p in permissions]
    }

@router.get("/users", response_model=list[User])
async def get_all_users(
    current_user: Dict[str, Any] = Depends(require_permission("view_users"))
) -> list:
    """
    Get all users (requires view_users permission)
    """
    users = list_users()
    result = []
    
    for user in users:
        role = UserRole(user["role"])
        permissions = ROLE_PERMISSIONS.get(role, [])
        
        result.append({
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "is_active": user["is_active"],
            "created_at": user["created_at"],
            "updated_at": user["updated_at"],
            "last_login": user.get("last_login"),
            "permissions": [p.value for p in permissions]
        })
    
    return result

@router.put("/users/{username}", response_model=User)
async def update_user_by_admin(
    username: str,
    updates: UserUpdate,
    current_user: Dict[str, Any] = Depends(require_permission("manage_users"))
) -> Dict[str, Any]:
    """
    Update user by admin (requires manage_users permission)
    """
    updated_user = update_user(username, updates.dict(exclude_unset=True))
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    role = UserRole(updated_user["role"])
    permissions = ROLE_PERMISSIONS.get(role, [])
    
    return {
        "id": updated_user["id"],
        "username": updated_user["username"],
        "email": updated_user["email"],
        "full_name": updated_user["full_name"],
        "role": updated_user["role"],
        "is_active": updated_user["is_active"],
        "created_at": updated_user["created_at"],
        "updated_at": updated_user["updated_at"],
        "last_login": updated_user.get("last_login"),
        "permissions": [p.value for p in permissions]
    }

@router.delete("/users/{username}")
async def delete_user_by_admin(
    username: str,
    current_user: Dict[str, Any] = Depends(require_permission("manage_users"))
) -> Dict[str, str]:
    """
    Delete user by admin (requires manage_users permission)
    """
    if username == current_user["username"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete your own account"
        )
    
    if delete_user(username):
        return {"message": f"User {username} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="User not found")

@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_active_user)) -> Dict[str, str]:
    """
    Logout endpoint (client should discard token)
    """
    # In a real implementation, you might want to blacklist the token
    return {"message": "Logged out successfully"}

# Add missing import
from datetime import datetime
