# Node-RED Backup Manager

Simple web interface for managing Node-RED flows.json backup files with authentication integration.

## Features

- 📁 Browse backup files by installation
- 💾 Download specific backup files
- 🔍 View all backups across installations
- 🔐 Simple authentication via Node-RED
- 🌙 Dark/light theme support
- 📱 Responsive design

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure
Edit `auth.py` and change the secret:
```python
AUTH_SECRET = "your-secret-here"  # Change this!
```

Update backup directory in `main.py`:
```python
BACKUP_BASE_DIR = "/path/to/your/backups"
```

### 3. Run
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Access web interface: `http://localhost:8000/web`

## Backup Directory Structure

```
/home/kimbo/nodered-backups/
├── Installation_1/
│   ├── flows_20241215.json
│   └── flows_20241210.json
├── Installation_2/
│   └── flows_20241220.json
└── ...
```

## Node-RED Integration

1. Import `node-red-flow.json` into Node-RED
2. Update URLs in the flow to point to your backup manager
3. Access via: `http://your-nodered:1880/backup-manager`

## Production Deployment

### Using systemd (recommended)

1. Run install script:
```bash
sudo ./deploy/install.sh
```

2. Or manual setup:
```bash
# Create user
sudo useradd --system --shell /bin/false --home /opt/backup-manager --create-home backup-manager

# Copy files
sudo cp -r . /opt/backup-manager/
sudo chown -R backup-manager:backup-manager /opt/backup-manager

# Install systemd service
sudo cp deploy/backup-manager.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable backup-manager
sudo systemctl start backup-manager
```

3. Check status:
```bash
sudo systemctl status backup-manager
```

## API Endpoints

### Web Interface
- `GET /web` - Main interface
- `GET /web/installation/{name}` - Installation view
- `GET /web/all-backups` - All backups view

### Authentication
- `GET /auth` - Get auth hash (for Node-RED)
- `GET /login?auth=hash` - Login with hash
- `GET /logout` - Logout

### API (JSON)
- `GET /installations` - List installations
- `GET /installations/{name}/files` - List files for installation
- `GET /installations/{name}/latest` - Download latest backup
- `GET /installations/{name}/files/{filename}` - Download specific file
- `DELETE /installations/{name}/files/{filename}` - Delete file

## Configuration

### Environment Variables
- `BACKUP_DIR` - Override backup directory
- `AUTH_SECRET` - Override auth secret
- `PORT` - Override port (default: 8000)

### Security Notes
- Change `AUTH_SECRET` in production
- Use HTTPS in production
- Backup directory should be readable by the service user
- Access is controlled by Node-RED authentication

## Troubleshooting

### Check service logs:
```bash
sudo journalctl -u backup-manager -f
```

### Test API:
```bash
curl http://localhost:8000/health
```

### Reset authentication:
```bash
curl http://localhost:8000/logout
```

## License

MIT License