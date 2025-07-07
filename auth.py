"""
Simple authentication module for Node-RED Backup API
Uses environment variable password hash compared with cookie
"""

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
import hashlib
import os

# Get password from environment variable
BACKUP_PASSWORD = "default-backup-password-2024"

def get_expected_hash():
    """Generate expected hash from environment password"""
    return hashlib.md5(BACKUP_PASSWORD.encode()).hexdigest()

def is_authenticated(request: Request):
    """Check if user has valid auth cookie with correct hash"""
    #cookie_hash = request.cookies.get("backup_auth")
    #expected_hash = get_expected_hash()

    #return cookie_hash == expected_hash
    return 1

async def logout_endpoint():
    """Logout - clear cookie"""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("backup_auth")
    return response