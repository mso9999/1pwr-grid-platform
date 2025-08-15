# Deployment Guide

## Overview

This guide covers deployment of the 1PWR Grid Platform to production environments.

## Deployment Architecture

```
                    ┌─────────────┐
                    │   Nginx     │
                    │ (Port 80/443)│
                    └──────┬──────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
     ┌──────▼──────┐             ┌────────▼────────┐
     │  Frontend   │             │    Backend API   │
     │  (Port 3000)│             │    (Port 8000)  │
     └─────────────┘             └────────┬────────┘
                                          │
                                 ┌────────▼────────┐
                                 │   PostgreSQL    │
                                 │   Database      │
                                 └─────────────────┘
```

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Docker and Docker Compose (recommended)
- OR Python 3.10+ and Node.js 18+ for manual deployment
- PostgreSQL 14+ with PostGIS extension
- Domain name with SSL certificate

## Docker Deployment (Recommended)

### 1. Create Docker Files

**Backend Dockerfile:**
```dockerfile
# backend/Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY ../modules /app/modules

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**
```dockerfile
# web-app/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
RUN npm ci --production

CMD ["npm", "start"]
```

### 2. Docker Compose Configuration

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgis/postgis:14-3.2
    environment:
      POSTGRES_DB: ugrid_platform
      POSTGRES_USER: ugrid_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - ugrid_network

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://ugrid_user:${DB_PASSWORD}@postgres:5432/ugrid_platform
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      - postgres
    networks:
      - ugrid_network
    ports:
      - "8000:8000"

  frontend:
    build: ./web-app
    environment:
      NEXT_PUBLIC_API_URL: ${API_URL}
    depends_on:
      - backend
    networks:
      - ugrid_network
    ports:
      - "3000:3000"

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - frontend
      - backend
    networks:
      - ugrid_network

volumes:
  postgres_data:

networks:
  ugrid_network:
```

### 3. Deploy with Docker

```bash
# Set environment variables
export DB_PASSWORD=your_secure_password
export SECRET_KEY=your_secret_key
export API_URL=https://api.yourdomain.com

# Build and start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Manual Deployment

### 1. System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3.10 python3.10-venv python3-pip nodejs npm nginx postgresql postgresql-contrib postgis -y

# Install PM2 for process management
sudo npm install -g pm2
```

### 2. Database Setup

```bash
# Create database and user
sudo -u postgres psql
CREATE DATABASE ugrid_platform;
CREATE USER ugrid_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ugrid_platform TO ugrid_user;
CREATE EXTENSION postgis;
\q
```

### 3. Backend Deployment

```bash
# Clone repository
git clone https://github.com/1pwr/1pwr-grid-platform.git
cd 1pwr-grid-platform

# Setup Python environment
python3.10 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Install production server
pip install gunicorn

# Create systemd service
sudo nano /etc/systemd/system/ugrid-backend.service
```

**ugrid-backend.service:**
```ini
[Unit]
Description=1PWR Grid Platform Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/1pwr-grid-platform/backend
Environment="PATH=/home/ubuntu/1pwr-grid-platform/venv/bin"
ExecStart=/home/ubuntu/1pwr-grid-platform/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

```bash
# Start backend service
sudo systemctl enable ugrid-backend
sudo systemctl start ugrid-backend
```

### 4. Frontend Deployment

```bash
cd web-app

# Install dependencies
npm ci

# Build production version
npm run build

# Start with PM2
pm2 start npm --name "ugrid-frontend" -- start
pm2 save
pm2 startup
```

### 5. Nginx Configuration

**/etc/nginx/sites-available/ugrid-platform:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ugrid-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://ugrid_user:password@localhost:5432/ugrid_platform
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=["https://yourdomain.com"]
ENVIRONMENT=production
```

### Frontend (.env.production)
```
NEXT_PUBLIC_API_URL=https://yourdomain.com
NEXT_PUBLIC_MAP_TILES_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
```

## SSL Certificate Setup

### Using Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

## Monitoring

### Health Checks
```bash
# Backend health
curl https://yourdomain.com/api/health

# Frontend health
curl https://yourdomain.com/
```

### Logs
```bash
# Backend logs
sudo journalctl -u ugrid-backend -f

# Frontend logs
pm2 logs ugrid-frontend

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Backup Strategy

### Database Backup
```bash
# Create backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump ugrid_platform > /backups/ugrid_backup_$DATE.sql

# Add to crontab for daily backups
0 2 * * * /home/ubuntu/backup.sh
```

### File Backup
```bash
# Backup uploaded files and data
tar -czf /backups/ugrid_files_$(date +%Y%m%d).tar.gz /var/ugrid/uploads
```

## Scaling

### Horizontal Scaling
1. Add load balancer (HAProxy/Nginx)
2. Deploy multiple backend instances
3. Use Redis for session storage
4. Configure database replication

### Vertical Scaling
1. Increase server resources
2. Optimize database queries
3. Add caching layer (Redis/Memcached)
4. Use CDN for static assets

## Security Checklist

- [ ] SSL certificate installed
- [ ] Firewall configured (UFW/iptables)
- [ ] Database password secured
- [ ] Secret keys rotated
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Regular security updates
- [ ] Backup strategy implemented
- [ ] Monitoring alerts configured
- [ ] Log rotation configured

## Troubleshooting

### Service Won't Start
```bash
# Check service status
sudo systemctl status ugrid-backend
pm2 status

# Check logs
sudo journalctl -xe
pm2 logs
```

### Database Connection Issues
```bash
# Test connection
psql -h localhost -U ugrid_user -d ugrid_platform

# Check PostgreSQL status
sudo systemctl status postgresql
```

### Performance Issues
```bash
# Monitor resources
htop
iostat -x 1
netstat -tulpn
```

## Rollback Procedure

1. Stop services
```bash
sudo systemctl stop ugrid-backend
pm2 stop ugrid-frontend
```

2. Restore database
```bash
psql ugrid_platform < /backups/ugrid_backup_YYYYMMDD.sql
```

3. Restore code
```bash
git checkout previous-version-tag
```

4. Restart services
```bash
sudo systemctl start ugrid-backend
pm2 start ugrid-frontend
```
