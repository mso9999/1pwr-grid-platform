#!/usr/bin/env python3
"""
Test script for authentication endpoints
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_login():
    """Test login with default credentials"""
    print("\n1. Testing Login...")
    
    # Test with form data (OAuth2 standard)
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"✓ Login successful")
        print(f"  - Access token: {token_data['access_token'][:50]}...")
        print(f"  - Token type: {token_data['token_type']}")
        print(f"  - Expires in: {token_data['expires_in']} seconds")
        return token_data['access_token']
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

def test_get_current_user(token):
    """Test getting current user info"""
    print("\n2. Testing Get Current User...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"✓ Current user retrieved")
        print(f"  - Username: {user_data['username']}")
        print(f"  - Email: {user_data['email']}")
        print(f"  - Role: {user_data['role']}")
        print(f"  - Permissions: {len(user_data['permissions'])} permissions")
        return user_data
    else:
        print(f"✗ Failed to get user: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

def test_list_users(token):
    """Test listing all users (requires admin)"""
    print("\n3. Testing List Users...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/auth/users", headers=headers)
    
    if response.status_code == 200:
        users = response.json()
        print(f"✓ Users listed: {len(users)} users found")
        for user in users:
            print(f"  - {user['username']} ({user['role']}): {user['full_name']}")
        return users
    else:
        print(f"✗ Failed to list users: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

def test_invalid_login():
    """Test login with invalid credentials"""
    print("\n4. Testing Invalid Login...")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={
            "username": "admin",
            "password": "wrongpassword"
        }
    )
    
    if response.status_code == 401:
        print(f"✓ Invalid login correctly rejected")
        return True
    else:
        print(f"✗ Unexpected response: {response.status_code}")
        print(f"  Response: {response.text}")
        return False

def test_permission_denied():
    """Test accessing protected endpoint without proper permissions"""
    print("\n5. Testing Permission Denied...")
    
    # First login as viewer (limited permissions)
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={
            "username": "viewer",
            "password": "viewer123"
        }
    )
    
    if response.status_code == 200:
        token = response.json()['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access admin-only endpoint
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            headers=headers,
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
                "full_name": "New User",
                "role": "viewer"
            }
        )
        
        if response.status_code == 403:
            print(f"✓ Permission correctly denied for viewer role")
            return True
        else:
            print(f"✗ Unexpected response: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    else:
        print(f"✗ Could not login as viewer: {response.status_code}")
        return False

def main():
    """Run all authentication tests"""
    print("=" * 60)
    print("Testing Authentication Endpoints")
    print("=" * 60)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("ERROR: Backend server is not responding properly")
            print("Please start the backend server first:")
            print("  cd backend && python main.py")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend server at", BASE_URL)
        print("Please start the backend server first:")
        print("  cd backend && python main.py")
        sys.exit(1)
    
    # Run tests
    token = test_login()
    if token:
        test_get_current_user(token)
        test_list_users(token)
    
    test_invalid_login()
    test_permission_denied()
    
    print("\n" + "=" * 60)
    print("Authentication Tests Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
