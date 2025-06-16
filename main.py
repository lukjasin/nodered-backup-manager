from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path
from datetime import datetime

# Import simple auth functions
from auth import is_authenticated, logout_endpoint

# Where we keep all the backups
BACKUP_BASE_DIR = "/home/kimbo/nodered-backups"

# Start up FastAPI
app = FastAPI(title="Node-RED Backup API", version="1.0.0")

# Templates for Jinja2 - auto reload in development
templates = Jinja2Templates(directory="templates", auto_reload=True)


def get_backup_path():
    """Just returns the path to backup folder"""
    return Path(BACKUP_BASE_DIR)


def validate_installation_name(installation: str):
    """Make sure nobody tries funny business with folder names"""
    if not installation or ".." in installation or "/" in installation or "\\" in installation:
        raise HTTPException(status_code=400, detail="That installation name looks sketchy")


# === AUTH ENDPOINTS ===

@app.get("/logout")
async def logout():
    """Logout - clear cookie"""
    return await logout_endpoint()


# === WEB INTERFACE ===

@app.get("/", response_class=HTMLResponse)
async def web_interface(request: Request):
    """Main web interface for managing backups"""
    # Check auth
    if not is_authenticated(request):
        return templates.TemplateResponse("login.html", {"request": request})

    try:
        installations = []
        backup_path = get_backup_path()

        if backup_path.exists():
            for item in backup_path.iterdir():
                if item.is_dir():
                    installations.append(item.name)

        installations.sort()

        return templates.TemplateResponse("index.html", {
            "request": request,
            "installations": installations,
            "user": {"authenticated": True}
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "installations": [],
            "error": str(e),
            "user": {"authenticated": True}
        })


@app.get("/installation/{installation_name}", response_class=HTMLResponse)
async def installation_view(request: Request, installation_name: str):
    """Web view for specific installation"""
    # Check auth
    if not is_authenticated(request):
        return templates.TemplateResponse("login.html", {"request": request})

    validate_installation_name(installation_name)

    try:
        installation_path = get_backup_path() / installation_name

        if not installation_path.exists():
            raise HTTPException(status_code=404, detail=f"Installation '{installation_name}' doesn't exist")

        files = []
        for file_path in installation_path.glob("*.json"):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime),
                    "installation": installation_name
                })

        files.sort(key=lambda x: x["modified"], reverse=True)

        # Get all installations for sidebar
        all_installations = []
        backup_path = get_backup_path()
        if backup_path.exists():
            for item in backup_path.iterdir():
                if item.is_dir():
                    all_installations.append(item.name)
        all_installations.sort()

        return templates.TemplateResponse("installation.html", {
            "request": request,
            "installation_name": installation_name,
            "files": files,
            "installations": all_installations,
            "user": {"authenticated": True}
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")


@app.get("/all-backups", response_class=HTMLResponse)
async def all_backups_view(request: Request):
    """Web view for all backups"""
    # Check auth
    if not is_authenticated(request):
        return templates.TemplateResponse("login.html", {"request": request})

    try:
        installations = []
        backup_path = get_backup_path()

        if backup_path.exists():
            for item in backup_path.iterdir():
                if item.is_dir():
                    installations.append(item.name)

        installations.sort()

        all_files = []
        for installation in installations:
            try:
                installation_path = backup_path / installation
                for file_path in installation_path.glob("*.json"):
                    if file_path.is_file():
                        stat = file_path.stat()
                        all_files.append({
                            "filename": file_path.name,
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime),
                            "installation": installation
                        })
            except Exception as e:
                print(f"Error loading files for {installation}: {e}")

        all_files.sort(key=lambda x: x["modified"], reverse=True)

        return templates.TemplateResponse("all_backups.html", {
            "request": request,
            "files": all_files,
            "installations": installations,
            "user": {"authenticated": True}
        })
    except Exception as e:
        return templates.TemplateResponse("all_backups.html", {
            "request": request,
            "files": [],
            "installations": [],
            "error": str(e),
            "user": {"authenticated": True}
        })


# === API ENDPOINTS (for file downloads only) ===

@app.get("/api/installations/{installation}/latest")
def get_latest_backup(installation: str, request: Request):
    """Download the newest backup file with its original name"""
    # Check auth for API endpoints too
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    validate_installation_name(installation)

    installation_path = get_backup_path() / installation

    if not installation_path.exists():
        raise HTTPException(status_code=404, detail=f"Installation '{installation}' doesn't exist")

    try:
        json_files = list(installation_path.glob("*.json"))

        if not json_files:
            raise HTTPException(status_code=404, detail=f"No JSON files in installation '{installation}'")

        latest_file = max(json_files, key=lambda x: x.stat().st_mtime)

        return FileResponse(
            path=str(latest_file),
            filename=latest_file.name,
            media_type='application/json'
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong finding the latest file: {str(e)}")


@app.get("/api/installations/{installation}/files/{filename}")
def download_specific_backup(installation: str, filename: str, request: Request):
    """Download a specific backup file by name"""
    # Check auth for API endpoints too
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    validate_installation_name(installation)

    if not filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Can only download .json files")

    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="That filename looks sketchy")

    file_path = get_backup_path() / installation / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File '{filename}' doesn't exist in installation '{installation}'")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail=f"'{filename}' is not a file")

    try:
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/json'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong downloading the file: {str(e)}")


@app.delete("/api/installations/{installation}/files/{filename}")
def delete_backup(installation: str, filename: str, request: Request):
    """Delete a specific backup file"""
    # Check auth for API endpoints too
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    validate_installation_name(installation)

    if not filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Can only delete .json files")

    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="That filename looks sketchy")

    file_path = get_backup_path() / installation / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File '{filename}' doesn't exist in installation '{installation}'")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail=f"'{filename}' is not a file")

    try:
        file_path.unlink()

        return {
            "message": "File deleted successfully",
            "installation": installation,
            "filename": filename,
            "deleted_at": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong deleting the file: {str(e)}")


# === HEALTH CHECK ===

@app.get("/health")
def health_check():
    """Health check - see if API is working and backup folder is accessible"""
    backup_path = get_backup_path()

    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "backup_dir": BACKUP_BASE_DIR,
        "backup_dir_exists": backup_path.exists(),
        "backup_dir_readable": backup_path.exists() and os.access(backup_path, os.R_OK),
        "backup_dir_writable": backup_path.exists() and os.access(backup_path, os.W_OK)
    }