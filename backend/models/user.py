"""
User model for authentication and authorization
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    PROCUREMENT = "procurement"
    REQUESTOR = "requestor"
    FIELD_TEAM = "field_team"
    VIEWER = "viewer"

class UserPermission(str, Enum):
    """User permission enumeration"""
    # Network operations
    VIEW_NETWORK = "view_network"
    EDIT_NETWORK = "edit_network"
    DELETE_NETWORK = "delete_network"
    IMPORT_DATA = "import_data"
    EXPORT_DATA = "export_data"
    
    # As-built operations
    SUBMIT_ASBUILT = "submit_asbuilt"
    APPROVE_ASBUILT = "approve_asbuilt"
    
    # User management
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    
    # System administration
    SYSTEM_ADMIN = "system_admin"
    VIEW_LOGS = "view_logs"

# Role to permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        UserPermission.VIEW_NETWORK,
        UserPermission.EDIT_NETWORK,
        UserPermission.DELETE_NETWORK,
        UserPermission.IMPORT_DATA,
        UserPermission.EXPORT_DATA,
        UserPermission.SUBMIT_ASBUILT,
        UserPermission.APPROVE_ASBUILT,
        UserPermission.MANAGE_USERS,
        UserPermission.VIEW_USERS,
        UserPermission.SYSTEM_ADMIN,
        UserPermission.VIEW_LOGS
    ],
    UserRole.PROCUREMENT: [
        UserPermission.VIEW_NETWORK,
        UserPermission.EDIT_NETWORK,
        UserPermission.IMPORT_DATA,
        UserPermission.EXPORT_DATA,
        UserPermission.APPROVE_ASBUILT,
        UserPermission.VIEW_USERS
    ],
    UserRole.REQUESTOR: [
        UserPermission.VIEW_NETWORK,
        UserPermission.EXPORT_DATA
    ],
    UserRole.FIELD_TEAM: [
        UserPermission.VIEW_NETWORK,
        UserPermission.SUBMIT_ASBUILT,
        UserPermission.EXPORT_DATA
    ],
    UserRole.VIEWER: [
        UserPermission.VIEW_NETWORK
    ]
}

class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.VIEWER
    is_active: bool = True

class UserCreate(UserBase):
    """User creation model"""
    password: str = Field(..., min_length=8, max_length=100)

class UserUpdate(BaseModel):
    """User update model"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)

class User(UserBase):
    """User model with all fields"""
    id: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    permissions: List[UserPermission] = []
    
    class Config:
        orm_mode = True

class UserInDB(User):
    """User model stored in database"""
    hashed_password: str

class UserLogin(BaseModel):
    """User login model"""
    username: str
    password: str

class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 3600

class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None
    permissions: List[str] = []
